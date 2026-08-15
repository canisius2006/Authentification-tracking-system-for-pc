import win32gui
import win32con
import win32process
import psutil
import json


TITRE_INCONNU = "Titre inconnu"


def _get_application_depuis_hwnd(hwnd):
    """Retourne (application, titre, pid) pour un handle de fenêtre donné."""
    titre = win32gui.GetWindowText(hwnd).strip() or TITRE_INCONNU
    _, pid = win32process.GetWindowThreadProcessId(hwnd)

    try:
        processus = psutil.Process(pid)
        application = processus.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        application = "Inconnu"

    return application, titre, pid


def _est_fenetre_utilisateur(hwnd):
    """
    Détermine si une fenêtre fait partie de celles qu'un utilisateur
    verrait réellement à l'écran (type liste alt-tab), indépendamment
    du fait qu'elle ait un titre ou non.

    Règles :
    - doit être visible
    - doit être une fenêtre top-level sans "owner" (élimine les popups,
      tooltips, menus, boîtes de dialogue secondaires)
    - exclue si elle a le style WS_EX_TOOLWINDOW (barres d'outils/palettes),
      sauf si elle a aussi WS_EX_APPWINDOW (forcée à apparaître dans l'alt-tab)
    """
    if not win32gui.IsWindowVisible(hwnd):
        return False

    if win32gui.GetWindow(hwnd, win32con.GW_OWNER) != 0:
        return False

    style_etendu = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    est_tool_window = bool(style_etendu & win32con.WS_EX_TOOLWINDOW)
    est_app_window = bool(style_etendu & win32con.WS_EX_APPWINDOW)

    if est_tool_window and not est_app_window:
        return False

    return True


def applications_premier_plan():
    """
    Énumère toutes les fenêtres actuellement visibles par l'utilisateur
    (liste type alt-tab), et retourne une liste de dicts {application, titre}.
    Les fenêtres sans titre (jeux plein écran, PiP, etc.) sont conservées
    avec "Titre inconnu" plutôt qu'exclues.
    """
    resultats = []

    def _callback(hwnd, _):
        if not _est_fenetre_utilisateur(hwnd):
            return True

        application, titre, pid = _get_application_depuis_hwnd(hwnd)

        resultats.append({
            "hwnd": hwnd,
            "application": application,
            "titre": titre
        })
        return True

    win32gui.EnumWindows(_callback, None)
    return resultats


def application_active():
    """
    Retourne l'application actuellement active (au premier plan / focus),
    sous forme de dict {hwnd, application, titre}, ou None si indisponible.
    """
    hwnd = win32gui.GetForegroundWindow()

    if not hwnd or not win32gui.IsWindowVisible(hwnd):
        return None

    application, titre, pid = _get_application_depuis_hwnd(hwnd)

    return {
        "hwnd": hwnd,
        "application": application,
        "titre": titre
    }


def etat_applications():
    """
    Fusionne les deux sources :
    - toutes les applications visibles par l'utilisateur (premier plan)
    - l'application active

    Si l'application active est déjà présente dans la liste des applications
    visibles (même hwnd), elle n'est pas dupliquée : elle est simplement
    incluse une seule fois dans la liste finale.
    """
    apps = applications_premier_plan()
    active = application_active()

    if active is not None:
        deja_present = any(app["hwnd"] == active["hwnd"] for app in apps)
        if not deja_present:
            apps.insert(0, active)

    # on ne garde que les champs demandés (application, titre) dans le résultat final
    applications = [
        {"application": app["application"], "titre": app["titre"]}
        for app in apps
    ]

    return json.dumps({
        "applications": applications
    }, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    print(etat_applications())
