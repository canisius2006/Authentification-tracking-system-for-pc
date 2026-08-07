from celery import shared_task
from django.db import transaction

from .models import Application, Bad_action
from .analyseur import analyser_activite
import json 

@shared_task
def verifier_activite(application_id, activite):
    """
    Analyse une activité et crée une Bad_action uniquement
    si l'analyseur indique que l'activité est mauvaise.
    """
    
    # 1. Récupérer l'application
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        return {
            "success": False,
            "message": "Application introuvable."
        }

    # 2. Analyser l'activité
    resultat = dict(analyser_activite(json.loads(activite)))

    # 3. L'activité n'est pas mauvaise => rien à créer
    if resultat.get("mauvais") is not True:
        return {
            "success": True,
            "bad_action_created": False,
            "message": "Activité autorisée."
        }

    # 4. L'activité est mauvaise => créer Bad_action
    with transaction.atomic():

        bad_action, created = Bad_action.objects.get_or_create(
            application=application,
            titre=resultat.get("title", ""),
            text_input=activite,
            defaults={
                "justification": resultat.get("justification", "")
            }
        )

    return {
        "success": True,
        "bad_action_created": created,
        "bad_action_id": bad_action.id
    }
