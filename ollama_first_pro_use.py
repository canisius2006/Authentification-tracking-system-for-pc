import ollama
import json
{}
activite = {
    'application': 'chrome.exe', 'titre': 'moondream - Google Chrome',
    'keylogging':'télécharger le modèle Qween'

}

SYSTEM_PROMPT = """Tu analyses l'activité d'un utilisateur dans un centre éducatif.

Objectif du centre : apprendre, programmer, faire des recherches.

Règles de pénalité (0 à 5 points) :
- 0 = activité éducative (cours, code, documentation technique, installation de bibliothèques,
      compilation, débogage, recherche académique, etc.)
- 1-2 = divertissement léger (musique en fond, réseaux sociaux informatifs, pauses courtes)
- 3-5 = activité clairement hors-sujet ou nuisible (jeux vidéo, streaming vidéo, réseaux sociaux
      de loisir, contenu inapproprié)

Important :
- Tout ce qui touche à la programmation (éditeurs de code, terminal, pip/npm/git, documentation
  technique, Stack Overflow, IDE) est TOUJOURS éducatif (0 point), même si le titre de la fenêtre
  semble être une simple commande technique.
- "mauvais" doit être cohérent avec "point_a_enlever" : si mauvais=false alors point_a_enlever=0,
  si mauvais=true alors point_a_enlever doit être entre 1 et 5.

Réponds STRICTEMENT en JSON valide, sans commentaire, avec exactement ce format :
{
    "title": "description courte",
    "mauvais": false,
    "point_a_enlever": 0,
    "justification": "une phrase"
}

Exemples :
Activité: {"application": "code.exe", "titre": "pip install customtkinter"}
Réponse: {"title": "Installation d'une bibliothèque Python", "mauvais": false, "point_a_enlever": 0, "justification": "L'installation de packages via pip fait partie du travail de programmation."}

Activité: {"application": "chrome.exe", "titre": "YouTube - Let's Play Minecraft"}
Réponse: {"title": "Visionnage de contenu de divertissement", "mauvais": true, "point_a_enlever": 4, "justification": "Le contenu regardé n'a aucun lien avec l'apprentissage ou la programmation."}
"""


def analyser_activite(activite: dict, max_tentatives: int = 2) -> dict:
    user_prompt = f"Activité: {json.dumps(activite, ensure_ascii=False)}"

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

            # Validation / normalisation des champs
            data.setdefault("title", activite.get("titre", ""))
            data["mauvais"] = bool(data.get("mauvais", False))
            point = data.get("point_a_enlever", 0)
            try:
                point = int(point)
            except (TypeError, ValueError):
                point = 0
            point = max(0, min(5, point))

            # Cohérence forcée entre mauvais et point_a_enlever
            if not data["mauvais"]:
                point = 0
            elif point == 0:
                point = 1  # mauvais=true implique au moins 1 point

            data["point_a_enlever"] = point
            data.setdefault("justification", "")

            return data

        except (json.JSONDecodeError, KeyError) as e:
            if tentative == max_tentatives - 1:
                # Fallback sûr si le modèle échoue systématiquement
                return {
                    "title": activite.get("titre", ""),
                    "mauvais": False,
                    "point_a_enlever": 0,
                    "justification": f"Analyse impossible ({e}), activité non pénalisée par défaut.",
                }
            continue


data = analyser_activite(activite)

print(json.dumps(data, indent=4, ensure_ascii=False))