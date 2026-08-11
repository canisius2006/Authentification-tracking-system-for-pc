from celery import shared_task
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Application, Bad_action
from .analyseur import analyser_activite



@shared_task
def verifier_activite(application_id, activite):
    """
    Analyse une activité et crée une Bad_action uniquement
    si l'analyseur indique que l'activité est mauvaise.
    """
    
    print(activite)
    print(type(activite))

    if isinstance(activite,str):
        print("ce n'est pas un dict")
        return
   
    print('\n\n\n')
    # 1. Récupérer l'application
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        return {
            "success": False,
            "message": "Application introuvable."
        }

    # 2. Analyser l'activité
    resultat = dict(analyser_activite(activite))

    print(resultat)

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
                "justification": resultat
            }
        )

        # 5. Si une nouvelle Bad_action a été créée, on retire 1 points au score de l'utilisateur
        if created:
            user = application.session.user
            user.score = F('score') - 1
            user.save(update_fields=['score'])
            print("Created and i substracted the user's score")

        # 6. Dans tous les cas (nouvelle action ou doublon), on met à jour les heures de fin
        session = application.session
        session.heure_fin = timezone.now().time()
        application.heure_fin = timezone.now().time()

        session.save(update_fields=['heure_fin'])
        application.save(update_fields=['heure_fin'])

    return {
        "success": True,
        "bad_action_created": created,
        "bad_action_id": bad_action.id
    }
