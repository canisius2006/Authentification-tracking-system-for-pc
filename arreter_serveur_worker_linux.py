import os
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(BASE_DIR, ".worker_pids")

if not os.path.isfile(PID_FILE):
    print("Aucun fichier de PID trouvé, rien à arrêter.")
    exit()

with open(PID_FILE) as f:
    lignes = [l.strip() for l in f if l.strip()]

for ligne in lignes:
    nom, pid = ligne.split(":")
    pid = int(pid)
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"{nom} (PID {pid}) arrêté.")
    except ProcessLookupError:
        print(f"{nom} (PID {pid}) déjà arrêté.")

os.remove(PID_FILE)
