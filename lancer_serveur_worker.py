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


# ============================================================
# ENVIRONNEMENT VIRTUEL
# ============================================================

VENV_DIR = os.path.join(BASE_DIR, "venv")

PYTHON_EXE = os.path.join(
    VENV_DIR,
    "Scripts",
    "python.exe"
)

CELERY_EXE = os.path.join(
    VENV_DIR,
    "Scripts",
    "celery.exe"
)

WAITRESS_EXE = os.path.join(
    VENV_DIR,
    "Scripts",
    "waitress-serve.exe"
)


# ============================================================
# PROJET DJANGO
# ============================================================

DJANGO_DIR = os.path.join(
    BASE_DIR,
    "serveur",
    "authentification"
)

MANAGE_PY = os.path.join(
    DJANGO_DIR,
    "manage.py"
)


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
        raise FileNotFoundError(
            f"{name} introuvable : {path}"
        )


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

ouvrir_terminal(
    "WAITRESS - 8000",
    commande_waitress,
    DJANGO_DIR
)


# ============================================================
# 2. CELERY
# ============================================================

commande_celery = (
    f'& "{CELERY_EXE}" '
    f'-A {CELERY_APP} '
    f'worker -l info --pool=solo'
)

ouvrir_terminal(
    "CELERY WORKER",
    commande_celery,
    DJANGO_DIR
)


# ============================================================
# FIN
# ============================================================

print(
    "Waitress et Celery ont été lancés "
    "dans deux fenêtres séparées."
)