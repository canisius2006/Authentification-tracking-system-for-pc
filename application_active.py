import win32gui
import win32process
import psutil
import time 
time.sleep(3)
def application_active():

    # Récupérer la fenêtre active
    hwnd = win32gui.GetForegroundWindow()

    if hwnd == 0:
        return None


    # Nom de la fenêtre
    titre = win32gui.GetWindowText(hwnd)


    # Récupérer le PID du processus
    _, pid = win32process.GetWindowThreadProcessId(hwnd)


    try:
        processus = psutil.Process(pid)
        application = processus.name()

    except Exception:
        application = "Inconnu"


    return {
        "application": application,
        "titre": titre
    }



print(application_active())