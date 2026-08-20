from celery import shared_task
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from zoneinfo import ZoneInfo
from .models import Application, Bad_action
from .analyseur import analyser_activite
import json


def update(application):
    """Met à jour l'heure de fin de la session et de l'application avec le même timestamp."""
    heure_fin = timezone.now().astimezone(ZoneInfo("Africa/Porto-Novo")).time()
    session = application.session

    session.heure_fin = heure_fin
    application.heure_fin = heure_fin

    session.save(update_fields=['heure_fin'])
    application.save(update_fields=['heure_fin'])


@shared_task
def verifier_activite(application_id, activite):
    """
    Analyse une activité et crée/actualise une Bad_action uniquement
    si l'analyseur indique que l'activité est mauvaise.
    """
    print("=============================\n", activite, "\n=============================\n")

    # 1. Récupérer l'application
    try:
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        return {
            "success": False,
            "message": "Application introuvable."
        }

    # On garde une trace de l'état AVANT modification, pour ne pas fausser
    # la logique du bloc 4 une fois application.verified passé à True.
    deja_verifiee = application.verified
    resultat = None

    # 2. Analyser l'activité (seulement lors du tout premier passage)
    if not deja_verifiee:
        resultat = dict(analyser_activite(activite))
        application.justification = json.dumps(resultat)
        application.verified = True
        application.save(update_fields=['justification', 'verified'])

        # 3. L'activité n'est pas mauvaise => rien à créer
        if resultat.get("mauvais") is not True:
            update(application)
            return {
                "success": True,
                "bad_action_created": False,
                "message": "Activité autorisée."
            }

    # 4. L'activité est mauvaise (ou l'était déjà) => créer/actualiser la Bad_action
    with transaction.atomic():
        if not deja_verifiee:
            # Premier passage détecté comme mauvais : on crée la Bad_action initiale
            bad_action, created = Bad_action.objects.get_or_create(
                application=application,
                titre=resultat.get("title", ""),
                text_input=str(activite),
                defaults={
                    "justification": resultat
                }
            )
        else:
            # Passages suivants : l'application a déjà été jugée mauvaise auparavant
            bad_action = application.bad_actions.first()
            if bad_action is None:
                # Cas limite : verified=True mais aucune Bad_action associée
                # (ne devrait normalement pas arriver avec ce flux)
                update(application)
                return {
                    "success": True,
                    "bad_action_created": False,
                    "message": "Aucune mauvaise action à mettre à jour."
                }
            created = False

        # 5. Nouvelle Bad_action => on retire 1 point au score de l'utilisateur
        if created:
            user = application.session.user
            user.score = F('score') - 1
            user.save(update_fields=['score'])
        else:
            # Sinon, on incrémente le nombre de fois où l'infraction a été commise
            bad_action.nombre = F('nombre') + 1
            bad_action.save(update_fields=["nombre"])
            bad_action.refresh_from_db(fields=["nombre"])

            # Tous les 6 passages, pénalité supplémentaire pour persistance
            if bad_action.nombre % 6 == 0:
                user = application.session.user
                user.score = F('score') - 2
                user.save(update_fields=['score'])

        result = {
            "success": True,
            "bad_action_created": created,
            "bad_action_id": bad_action.id
        }

    # 6. Dans tous les cas (nouvelle action ou doublon), on met à jour les heures de fin
    update(application)
    return result
