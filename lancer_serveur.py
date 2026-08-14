import os
import socket
import shutil
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
if pc=='CIA-008':
    BASE_DIR = r"C:\developpement" 
    load_dotenv(r"C:\developpement\.env")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
    load_dotenv()

# Environnement virtuel
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

# Projet Django
DJANGO_DIR = os.path.join(
    BASE_DIR,
    "serveur",
    "authentification"
)

MANAGE_PY = os.path.join(
    DJANGO_DIR,
    "manage.py"
)

# Application Celery
CELERY_APP = "authentification"


# ============================================================
# VÉRIFICATION DES FICHIERS
# ============================================================

for path, name in [
    (PYTHON_EXE, "Python du venv"),
    (CELERY_EXE, "Celery"),
    (MANAGE_PY, "manage.py"),
]:
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"{name} introuvable : {path}"
        )


# ============================================================
# DÉTECTION DE REDIS / MEMURAI
# ============================================================

def trouver_redis_cli():
    """
    Cherche redis-cli et memurai-cli.

    Retourne le chemin du CLI qui fonctionne réellement.
    Retourne None si aucun ne fonctionne.
    """

    candidats = []

    # --------------------------------------------------------
    # 1. Recherche dans le PATH Windows
    # --------------------------------------------------------

    redis_path = shutil.which("redis-cli")
    memurai_path = shutil.which("memurai-cli")

    if redis_path:
        candidats.append(("redis-cli", redis_path))

    if memurai_path:
        candidats.append(("memurai-cli", memurai_path))

    # --------------------------------------------------------
    # 2. Quelques emplacements Windows courants
    # --------------------------------------------------------

    chemins_possibles = [
        ("redis-cli", r"C:\Redis\redis-cli.exe"),
        ("redis-cli", r"C:\Program Files\Redis\redis-cli.exe"),
        ("redis-cli", r"C:\Program Files\Redis\redis-cli.exe"),

        ("memurai-cli", r"C:\Program Files\Memurai\memurai-cli.exe"),
        ("memurai-cli", r"C:\Program Files\Memurai\bin\memurai-cli.exe"),
        ("memurai-cli", r"C:\Memurai\memurai-cli.exe"),
        ("memurai-cli", r"C:\Memurai\bin\memurai-cli.exe"),
    ]

    for nom, chemin in chemins_possibles:

        if os.path.isfile(chemin):

            # Évite les doublons
            if not any(
                chemin.lower() == c[1].lower()
                for c in candidats
            ):
                candidats.append((nom, chemin))

    # --------------------------------------------------------
    # 3. Tester chaque CLI
    # --------------------------------------------------------

    for nom, chemin in candidats:

        print(f"Test de {nom} : {chemin}")

        try:

            resultat = subprocess.run(
                [
                    chemin,
                    "-h"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Le programme existe et peut être exécuté
            if resultat.returncode in (0, 1, 2):

                print(f"{nom} trouvé.")

                # Maintenant on teste réellement Redis
                try:

                    ping = subprocess.run(
                        [
                            chemin,
                            "ping"
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    sortie = (
                        ping.stdout.strip()
                        + " "
                        + ping.stderr.strip()
                    ).upper()

                    if "PONG" in sortie:

                        print(
                            f"{nom} fonctionne correctement."
                        )

                        return chemin

                except (
                    subprocess.SubprocessError,
                    OSError
                ):
                    pass

        except (
            subprocess.SubprocessError,
            OSError
        ):
            pass

    return None


# ============================================================
# REDIS CLI
# ============================================================

REDIS_CLI = trouver_redis_cli()

if REDIS_CLI is None:

    raise RuntimeError(
        "\n"
        "==================================================\n"
        "ERREUR : aucun Redis CLI fonctionnel trouvé.\n"
        "==================================================\n"
        "\n"
        "Le script a essayé :\n"
        "  - redis-cli\n"
        "  - memurai-cli\n"
        "\n"
        "Vérifie que Redis ou Memurai est installé et\n"
        "que le serveur Redis fonctionne sur 127.0.0.1:6379.\n"
    )

print()
print("==================================================")
print("CLI Redis sélectionné :")
print(REDIS_CLI)
print("==================================================")
print()


# ============================================================
# HOST DJANGO
# ============================================================

db_host = os.getenv("DB_HOST")

if not db_host:
    raise RuntimeError(
        "DB_HOST n'est pas défini dans le fichier .env"
    )

try:

    host_ip = socket.gethostbyname(db_host)

except socket.gaierror:

    raise RuntimeError(
        f"Impossible de résoudre DB_HOST : {db_host}"
    )

HOST = f"{host_ip}:8000"


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
# 1. REDIS / MEMURAI CLI
# ============================================================

ouvrir_terminal(
    "REDIS - 6379",
    f'& "{REDIS_CLI}"',
    BASE_DIR
)


# ============================================================
# 2. DJANGO
# ============================================================

commande_django = (
    f'& "{PYTHON_EXE}" '
    f'"{MANAGE_PY}" '
    f'runserver {HOST}'
)

ouvrir_terminal(
    "DJANGO - 8000",
    commande_django,
    DJANGO_DIR
)


# ============================================================
# 3. CELERY
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


print(
    "Redis, Django et Celery ont été lancés "
    "dans trois fenêtres séparées."
)