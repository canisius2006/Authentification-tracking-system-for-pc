import json
import math
import ollama


# ============================================================
# 1. Normalisation de l'entrée
# ============================================================

def normaliser_activite(brut: dict) -> dict:
    application = brut.get("application", "inconnue")
    titre_parts = [str(v) for cle, v in brut.items() if cle != "application"]
    titre = " ".join(titre_parts).strip() or "sans titre"
    return {"application": application, "titre": titre}


# ============================================================
# 2. Porte de négation partagée
#    Appliquée une seule fois, avant toutes les couches. Si un mot de
#    contexte/négation apparaît, ni la blocklist ni les embeddings ne sont
#    fiables : seul le LLM comprend le sens réel de la phrase.
# ============================================================

MOTS_NEGATION_CONTEXTE = [
    "arrêter", "arreter", "stop", "addiction", "comment ne plus",
    "éviter de", "eviter de", "se débarrasser", "se debarrasser",
    "reportage sur", "documentaire sur", "cours sur", "histoire de",
    "pourquoi éviter", "pourquoi eviter",
]


def contient_negation(texte: str) -> bool:
    return any(mot in texte for mot in MOTS_NEGATION_CONTEXTE)


# ============================================================
# 3. Blocklist de domaines connus (Blocklist Project - piraterie/streaming)
#    Fichier à télécharger une fois : https://blocklistproject.github.io/Lists/piracy.txt
#    Format "hosts" (0.0.0.0 domaine.com) → on extrait juste les domaines.
# ============================================================

def charger_blocklist(chemin_fichier: str) -> set[str]:
    domaines = set()
    try:
        with open(chemin_fichier, encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#"):
                    continue
                parts = ligne.split()
                if len(parts) == 2:
                    domaines.add(parts[1].lower())
    except FileNotFoundError:
        pass  # fonctionne quand même sans, juste moins de couverture
    return domaines


BLOCKLIST_DOMAINES = charger_blocklist("piracy.txt")


def verifier_blocklist(activite: dict, texte: str) -> dict | None:
    for domaine in BLOCKLIST_DOMAINES:
        if domaine in texte:
            return {
                "title": activite["titre"],
                "mauvais": True,
                "confiance": 0.95,
                "justification": f"Domaine connu de streaming/piraterie détecté ({domaine}).",
                "methode": "blocklist",
            }
    return None


# ============================================================
# 4. Classification par similarité d'embeddings
#    Première ligne de jugement pour les cas non couverts par la blocklist :
#    stable, pas de contradiction possible, très rapide.
#    Modèle conseillé : "all-minilm" (~46 Mo, tourne bien sur CPU seul).
#    Installation : ollama pull all-minilm
# ============================================================

PROTOTYPES = {
    "educatif": [
        "installation d'une bibliothèque de programmation avec pip ou npm",
        "utilisation d'un éditeur de code ou d'un terminal",
        "documentation technique, tutoriel de programmation",
        "recherche académique, cours en ligne",
        "consultation ou téléchargement d'un modèle d'intelligence artificielle",
        "utilisation de git, github, contrôle de version",
    ],
    "divertissement": [
        "regarder un film ou une série en streaming",
        "regarder un anime ou un manga en streaming",
        "jouer à un jeu vidéo",
        "regarder des vidéos de divertissement sur YouTube",
        "réseaux sociaux de loisir, discussion informelle",
        "écouter de la musique pour se divertir",
    ],
}

_cache_embeddings_prototypes = None


def _embed(texte: str) -> list[float]:
    reponse = ollama.embeddings(model="all-minilm", prompt=texte)
    return reponse["embedding"]


def _cosine(a: list[float], b: list[float]) -> float:
    produit = sum(x * y for x, y in zip(a, b))
    norme_a = math.sqrt(sum(x * x for x in a))
    norme_b = math.sqrt(sum(y * y for y in b))
    if norme_a == 0 or norme_b == 0:
        return 0.0
    return produit / (norme_a * norme_b)


def _obtenir_embeddings_prototypes() -> dict[str, list[list[float]]]:
    global _cache_embeddings_prototypes
    if _cache_embeddings_prototypes is None:
        _cache_embeddings_prototypes = {
            categorie: [_embed(p) for p in phrases]
            for categorie, phrases in PROTOTYPES.items()
        }
    return _cache_embeddings_prototypes


def classifier_par_embeddings(activite: dict, texte: str, seuil_marge: float = 0.08) -> dict | None:
    embedding_activite = _embed(texte)
    prototypes = _obtenir_embeddings_prototypes()

    scores = {}
    for categorie, embeddings in prototypes.items():
        similarites = [_cosine(embedding_activite, e) for e in embeddings]
        scores[categorie] = max(similarites)

    score_educatif = scores["educatif"]
    score_divertissement = scores["divertissement"]
    marge = abs(score_educatif - score_divertissement)

    if marge < seuil_marge:
        return None  # trop ambigu, on laisse le LLM trancher en dernier recours

    mauvais = score_divertissement > score_educatif
    confiance = min(0.9, 0.5 + marge)

    return {
        "title": activite["titre"],
        "mauvais": mauvais,
        "confiance": round(confiance, 2),
        "justification": (
            f"Classé par similarité sémantique "
            f"(score éducatif={score_educatif:.2f}, divertissement={score_divertissement:.2f})."
        ),
        "methode": "embeddings",
    }


# ============================================================
# 5. LLM génératif — dernier recours, uniquement pour les cas ambigus
#    ou les cas contenant un mot de négation/contexte.
# ============================================================

SYSTEM_PROMPT = """Tu classes une activité informatique dans un centre éducatif
(objectif : apprendre, programmer, faire des recherches).

mauvais=false : programmation, IA, documentation technique, recherche légitime.
mauvais=true : divertissement (jeux, films, séries, réseaux sociaux de loisir).

Attention au sens réel de la phrase : "arrêter/éviter/reportage sur les mangas"
n'est PAS du divertissement, c'est une recherche sur le sujet. Juge l'intention,
pas juste la présence d'un mot comme "manga" ou "film".

Si le titre est trop vague pour juger (nom d'application seul, moteur de recherche
sans requête visible), réponds confiance basse (0.2-0.3) plutôt que de deviner.

JSON uniquement : {"title": "...", "mauvais": false, "confiance": 0.9, "justification": "..."}

Exemple :
{"application": "chrome.exe", "titre": "comment faire pour arrêter les mangas - Google Chrome"}
→ {"title": "Recherche sur l'arrêt d'une habitude", "mauvais": false, "confiance": 0.8, "justification": "La recherche porte sur comment arrêter, ce n'est pas de la consommation de divertissement."}
"""


def analyser_avec_llm(activite: dict, max_tentatives: int = 2) -> dict:
    user_prompt = json.dumps(activite, ensure_ascii=False)
    for tentative in range(max_tentatives):
        try:
            response = ollama.chat(
                model="qwen2.5:1.5b",
                format="json",
                options={"temperature": 0},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            data = json.loads(response["message"]["content"])
            data.setdefault("title", activite["titre"])
            data["mauvais"] = bool(data.get("mauvais", False))
            data["confiance"] = float(data.get("confiance", 0.5))
            data.setdefault("justification", "")
            data["methode"] = "llm"
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            if tentative == max_tentatives - 1:
                return {
                    "title": activite["titre"],
                    "mauvais": False,
                    "confiance": 0.0,
                    "justification": f"Analyse impossible ({e}).",
                    "methode": "fallback",
                }
            continue


# ============================================================
# Point d'entrée principal
# ============================================================

def analyser_activite(activite_brute: dict) -> dict:
    activite = normaliser_activite(activite_brute)
    texte = f"{activite['application']} {activite['titre']}".lower()

    # Porte de négation : appliquée une seule fois, avant toute couche rapide.
    if contient_negation(texte):
        return analyser_avec_llm(activite)

    resultat = verifier_blocklist(activite, texte)
    if resultat is not None:
        return resultat

    resultat = classifier_par_embeddings(activite, texte)
    if resultat is not None:
        return resultat

    return analyser_avec_llm(activite)


if __name__ == "__main__":
    cas_de_test = [
        {'application': 'Code.exe', 'titre': 'test.py - developpement - Visual Studio Code'},
        
    ]
    for activite_brute in cas_de_test:
        data = analyser_activite(activite_brute)
        print(json.dumps(data, indent=4, ensure_ascii=False))
        print("---")