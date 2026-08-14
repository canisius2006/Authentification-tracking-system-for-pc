import win32gui
import win32process
import psutil
import json


def application_premier_plan():
    # Récupère le handle de la fenêtre actuellement au premier plan
    hwnd = win32gui.GetForegroundWindow()

    if not hwnd:
        return None

    # Vérifie que la fenêtre est visible
    if not win32gui.IsWindowVisible(hwnd):
        return None

    # Titre de la fenêtre
    titre = win32gui.GetWindowText(hwnd)

    # Récupère le PID du processus associé à cette fenêtre
    _, pid = win32process.GetWindowThreadProcessId(hwnd)

    try:
        processus = psutil.Process(pid)

        # Nom de l'application/processus
        application = processus.name()

        # Chemin de l'exécutable, si accessible
        try:
            chemin = processus.exe()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            chemin = None

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        application = "Inconnu"
        chemin = None

    return json.dumps({
        "application": application,
        "titre": titre,
        "pid": pid,
        "chemin": chemin
    })


if __name__ == "__main__":
    resultat = application_premier_plan()

    print(json.dumps(
        resultat,
        ensure_ascii=False,
        indent=4
    ))