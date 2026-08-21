import os
import socket
import subprocess
from dotenv import load_dotenv


# ============================================================
# ENVIRONNEMENT
# ============================================================

pc = socket.gethostname()


# ============================================================
# CONFIGURATION
# ============================================================

# Dossier dans lequel se trouve lancer.py
if pc == "CIA-008":
    BASE_DIR = r"C:\developpement"
    load_dotenv(r"C:\developpement\.env")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    load_dotenv()

# Nombre de workers Celery à lancer en parallèle.
# Ajuste selon le nombre de coeurs CPU dispo et la charge attendue.
# Tu peux aussi le passer par variable d'environnement NB_WORKERS.
NB_WORKERS = int(os.environ.get("NB_WORKERS", 4))


# ============================================================
# ENVIRONNEMENT VIRTUEL
# ============================================================

VENV_DIR = os.path.join(BASE_DIR, "venv")

PYTHON_EXE = os.path.join(VENV_DIR, "Scripts", "python.exe")
CELERY_EXE = os.path.join(VENV_DIR, "Scripts", "celery.exe")
WAITRESS_EXE = os.path.join(VENV_DIR, "Scripts", "waitress-serve.exe")


# ============================================================
# PROJET DJANGO
# ============================================================

DJANGO_DIR = os.path.join(BASE_DIR, "serveur", "authentification")
MANAGE_PY = os.path.join(DJANGO_DIR, "manage.py")


# ============================================================
# APPLICATION CELERY
# ============================================================

CELERY_APP = "authentification"


# ============================================================
# VÉRIFICATION DES FICHIERS
# ============================================================

for path, name in [
    (PYTHON_EXE, "Python du venv"),
    (CELERY_EXE, "Celery"),
    (WAITRESS_EXE, "Waitress"),
    (MANAGE_PY, "manage.py"),
]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{name} introuvable : {path}")


# ============================================================
# OUVRIR UN NOUVEAU TERMINAL
# ============================================================

def ouvrir_terminal(titre, commande, dossier):
    """
    Ouvre une nouvelle fenêtre PowerShell indépendante.
    """
    powershell_command = (
        f'$Host.UI.RawUI.WindowTitle = "{titre}"; '
        f'Set-Location -LiteralPath "{dossier}"; '
        f'{commande}'
    )

    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-NoExit",
            "-Command",
            powershell_command
        ],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )


# ============================================================
# 1. WAITRESS
# ============================================================

commande_waitress = (
    f'& "{WAITRESS_EXE}" '
    f'--listen=0.0.0.0:8000 '
    f'authentification.wsgi:application'
)

ouvrir_terminal("WAITRESS - 8000", commande_waitress, DJANGO_DIR)


# ============================================================
# 2. CELERY - N WORKERS EN PARALLÈLE
# ============================================================
#
# Chaque worker tourne dans sa propre fenêtre PowerShell, avec un
# hostname unique (obligatoire sous Celery quand plusieurs workers
# consomment la même queue, sinon ils se marchent dessus).
#
# --pool=solo est conservé car c'est le seul pool fiable sous Windows
# (pas de fork). Pour paralléliser, on multiplie donc les PROCESS
# plutôt que les threads/greenlets internes à un seul worker.

for i in range(1, NB_WORKERS + 1):
    hostname = f"worker{i}@%h"

    commande_celery = (
        f'& "{CELERY_EXE}" '
        f'-A {CELERY_APP} '
        f'worker -l info --pool=solo '
        f'-n {hostname}'
    )

    ouvrir_terminal(f"CELERY WORKER {i}", commande_celery, DJANGO_DIR)


# ============================================================
# FIN
# ============================================================

print(
    f"Waitress et {NB_WORKERS} worker(s) Celery ont été lancés "
    f"dans des fenêtres séparées."
)

#Pour pouvoir lancer flower celery pour pouvoir voir les tâches en cours dans le navigateur
#celery -A authentification.celery flower
