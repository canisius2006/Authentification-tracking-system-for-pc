import os
import sys
import django

# 1. Indiquer à Python le dossier racine de votre projet
# (Ajustez le chemin si le dossier contenant settings.py est ailleurs)
sys.path.append(r"C:\developpement\serveur\authentification")

# 2. Configurer la variable d'environnement (remplacez 'authentification.settings' par votre vrai module)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'authentification.settings')
django.setup()

# 3. IMPORTS OBLIGATOIREMENT APRÈS django.setup()
from django.utils import timezone
from compte.models import  Session_activite

# 4. Traitement des données
date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
sessions = Session_activite.objects.filter(jour__lt=date)

for session in sessions:
    session.applications.update(verified=True)
        