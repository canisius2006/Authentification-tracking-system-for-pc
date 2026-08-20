import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Nombre de workers Celery à lancer en parallèle.
# Sous Linux, le fork fonctionne : tu peux AUSSI augmenter la
# concurrence d'un seul worker (--concurrency=N, pool prefork) au
# lieu de lancer N processus worker séparés. Les deux approches sont
# valables :
#   - N workers séparés (ce script) : isolation totale, logs séparés,
#     tu peux tuer/relancer un worker sans toucher aux autres.
#   - 1 worker --concurrency=N : plus simple, un seul processus à
#     superviser, mais tout s'arrête ensemble en cas de crash.
# Ici on garde N workers séparés pour rester cohérent avec la
# version Windows.
NB_WORKERS = int(os.environ.get("NB_WORKERS", 4))


# ============================================================
# ENVIRONNEMENT VIRTUEL
# ============================================================

VENV_DIR = os.path.join(BASE_DIR, "venv")

PYTHON_BIN = os.path.join(VENV_DIR, "bin", "python")
CELERY_BIN = os.path.join(VENV_DIR, "bin", "celery")
WAITRESS_BIN = os.path.join(VENV_DIR, "bin", "waitress-serve")


# ============================================================
# PROJET DJANGO
# ============================================================

DJANGO_DIR = os.path.join(BASE_DIR, "serveur", "authentification")
MANAGE_PY = os.path.join(DJANGO_DIR, "manage.py")

CELERY_APP = "authentification"

LOG_DIR = os.path.join(BASE_DIR, "logs")
PID_FILE = os.path.join(BASE_DIR, ".worker_pids")

Path(LOG_DIR).mkdir(exist_ok=True)


# ============================================================
# VÉRIFICATION DES FICHIERS
# ============================================================

for path, name in [
    (PYTHON_BIN, "Python du venv"),
    (CELERY_BIN, "Celery"),
    (WAITRESS_BIN, "Waitress"),
    (MANAGE_PY, "manage.py"),
]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{name} introuvable : {path}")


# ============================================================
# LANCER UN PROCESSUS EN ARRIÈRE-PLAN
# ============================================================

pids = []


def lancer_processus(nom, commande, dossier):
    """
    Lance un processus détaché (survit même si ce script se termine),
    avec ses logs redirigés dans un fichier dédié.
    """
    log_path = os.path.join(LOG_DIR, f"{nom}.log")
    log_file = open(log_path, "a")

    process = subprocess.Popen(
        commande,
        cwd=dossier,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,  # équivalent de setsid, détache du shell parent
    )

    pids.append((nom, process.pid))
    print(f"{nom} lancé (PID {process.pid}), logs -> {log_path}")


# ============================================================
# 1. WAITRESS
# ============================================================

lancer_processus(
    "waitress",
    [WAITRESS_BIN, "--listen=0.0.0.0:8000", "authentification.wsgi:application"],
    DJANGO_DIR,
)


# ============================================================
# 2. CELERY - N WORKERS EN PARALLÈLE
# ============================================================
#
# Sous Linux, le pool par défaut (prefork) fonctionne très bien,
# donc pas besoin de --pool=solo comme sous Windows.

for i in range(1, NB_WORKERS + 1):
    hostname = f"worker{i}@%h"

    lancer_processus(
        f"celery_worker_{i}",
        [
            CELERY_BIN, "-A", CELERY_APP,
            "worker", "-l", "info",
            "-n", hostname,
        ],
        DJANGO_DIR,
    )


# ============================================================
# SAUVEGARDE DES PID (pour pouvoir tout arrêter plus tard)
# ============================================================

with open(PID_FILE, "w") as f:
    for nom, pid in pids:
        f.write(f"{nom}:{pid}\n")


# ============================================================
# FIN
# ============================================================

print(
    f"\nWaitress et {NB_WORKERS} worker(s) Celery tournent en arrière-plan.\n"
    f"Logs dans : {LOG_DIR}\n"
    f"PIDs sauvegardés dans : {PID_FILE}\n"
    f"Pour tout arrêter, lance arreter_serveur_worker_linux.py"
)
