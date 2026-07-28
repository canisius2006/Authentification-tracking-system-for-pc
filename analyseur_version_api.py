import json
import math
import re
import time
import requests

t = time.time()

OLLAMA_URL = "http://localhost:11434"  # change l'IP ici si le serveur tourne ailleurs sur le réseau


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
# 3. Blocklist de domaines connus
# ============================================================

MOTIF_DOMAINE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z]{2,})+")


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
        pass
    return domaines


BLOCKLIST_DOMAINES = charger_blocklist("piracy.txt")


def verifier_blocklist(activite: dict, texte: str) -> dict | None:
    candidats = MOTIF_DOMAINE.findall(texte)
    for candidat in candidats:
        morceaux = candidat.split(".")
        for i in range(len(morceaux) - 1):
            suffixe = ".".join(morceaux[i:])
            if suffixe in BLOCKLIST_DOMAINES:
                return {
                    "title": activite["titre"],
                    "mauvais": True,
                    "confiance": 0.95,
                    "justification": f"Domaine connu de streaming/piraterie détecté ({suffixe}).",
                    "methode": "blocklist",
                }
    return None


# ============================================================
# 4. Classification par similarité d'embeddings
#    Appel HTTP direct à /api/embeddings, plus de dépendance au paquet ollama.
# ============================================================

MODELE_EMBEDDING = "bge-m3"  # remplace par "qwen2.5:1.5b" si tu préfères un seul modèle

SUFFIXES_NAVIGATEUR = [
    " - google chrome", " - mozilla firefox", " - microsoft edge",
    " - youtube", " - brave",
]


def nettoyer_pour_embedding(texte: str) -> str:
    texte_nettoye = texte.lower()
    for suffixe in SUFFIXES_NAVIGATEUR:
        texte_nettoye = texte_nettoye.replace(suffixe, "")
    return texte_nettoye.strip()


PROTOTYPES = {
    "educatif": [
        "installation d'une bibliothèque logicielle avec un gestionnaire de paquets",
        "édition de code source et développement logiciel",
        "documentation technique ou tutoriel de programmation",
        "cours ou explication pédagogique sur un sujet académique",
        "consultation ou téléchargement d'un modèle d'intelligence artificielle",
        "gestion de versions de code source",
    ],
    "divertissement": [
        "visionnage d'un film ou d'une série pour se divertir",
        "visionnage d'un anime ou d'un manga pour se divertir",
        "partie de jeu vidéo",
        "vidéo humoristique ou clip musical de loisir",
        "discussion informelle sur un réseau social",
        "écoute de musique pour le plaisir",
    ],
}

_cache_embeddings_prototypes = None


def _embed(texte: str) -> list[float]:
    """Appel HTTP direct, équivalent à ollama.embeddings(...)."""
    reponse = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": MODELE_EMBEDDING, "prompt": texte},
        timeout=30,
    )
    reponse.raise_for_status()
    return reponse.json()["embedding"]


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


def classifier_par_embeddings(
    activite: dict,
    texte: str,
    seuil_marge: float = 0.08,
    seuil_plancher: float = 0.30,
) -> dict | None:
    texte_propre = nettoyer_pour_embedding(texte)
    embedding_activite = _embed(texte_propre)
    prototypes = _obtenir_embeddings_prototypes()

    scores = {}
    for categorie, embeddings in prototypes.items():
        similarites = [_cosine(embedding_activite, e) for e in embeddings]
        scores[categorie] = max(similarites)

    score_educatif = scores["educatif"]
    score_divertissement = scores["divertissement"]
    marge = abs(score_educatif - score_divertissement)
    meilleur_score = max(score_educatif, score_divertissement)

    if marge < seuil_marge or meilleur_score < seuil_plancher:
        return None

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
# 5. LLM génératif — appel HTTP direct à /api/chat
# ============================================================

SEUIL_CONFIANCE = 0.55

SYSTEM_PROMPT = """Tu classes une activité informatique dans un centre éducatif
(objectif : apprendre, programmer, faire des recherches).

mauvais=false : programmation, IA, documentation technique, recherche légitime.
mauvais=true : divertissement (jeux, films, séries, réseaux sociaux de loisir).

Attention au sens réel de la phrase : "arrêter/éviter/reportage sur les mangas"
n'est PAS du divertissement, c'est une recherche sur le sujet.

Si le titre est trop vague pour juger, réponds confiance basse (0.2-0.3)
plutôt que de deviner.

JSON uniquement : {"title": "...", "mauvais": false, "confiance": 0.9, "justification": "..."}

Exemple :
{"application": "chrome.exe", "titre": "comment faire pour arrêter les mangas - Google Chrome"}
→ {"title": "Recherche sur l'arrêt d'une habitude", "mauvais": false, "confiance": 0.8, "justification": "La recherche porte sur comment arrêter, ce n'est pas de la consommation de divertissement."}
"""


def _incertain(activite: dict, justification: str) -> dict:
    return {
        "title": activite["titre"],
        "mauvais": None,
        "confiance": 0.0,
        "justification": justification,
        "methode": "incertain",
    }


def _appel_llm_unique(activite: dict, temperature: float) -> dict | None:
    """Appel HTTP direct, équivalent à ollama.chat(...)."""
    user_prompt = json.dumps(activite, ensure_ascii=False)
    try:
        reponse = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": "qwen2.5:1.5b",
                "format": "json",
                "stream": False,   # important : sans ça, l'API renvoie du texte en flux, pas un JSON unique
                "options": {"temperature": temperature},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=60,
        )
        reponse.raise_for_status()
        data = json.loads(reponse.json()["message"]["content"])
        return {
            "title": data.get("title", activite["titre"]),
            "mauvais": bool(data.get("mauvais", False)),
            "confiance": float(data.get("confiance", 0.5)),
            "justification": data.get("justification", ""),
        }
    except (requests.RequestException, json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def analyser_avec_llm(activite: dict) -> dict:
    premier = _appel_llm_unique(activite, temperature=0.0)
    if premier is None:
        return _incertain(activite, "Réponse du modèle illisible (JSON invalide ou serveur injoignable).")

    if premier["confiance"] < SEUIL_CONFIANCE:
        return _incertain(
            activite,
            f"Confiance du modèle trop basse ({premier['confiance']:.2f}) : {premier['justification']}",
        )

    second = _appel_llm_unique(activite, temperature=0.4)
    if second is None or second["mauvais"] != premier["mauvais"]:
        return _incertain(
            activite,
            "Deux évaluations du modèle ne concordent pas — cas ambigu, rejeté plutôt que deviné.",
        )

    confiance = round((premier["confiance"] + second["confiance"]) / 2, 2)
    return {
        "title": premier["title"],
        "mauvais": premier["mauvais"],
        "confiance": confiance,
        "justification": premier["justification"],
        "methode": "llm",
    }


# ============================================================
# Point d'entrée principal
# ============================================================

def analyser_activite(activite_brute: dict) -> dict:
    activite = normaliser_activite(activite_brute)
    texte = f"{activite['application']} {activite['titre']}".lower()

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

print(time.time() - t, 'secondes')