import win32gui
import win32process
import win32con
import psutil
import ctypes
from ctypes import wintypes
import json


DWMWA_CLOAKED = 14


# ============================================================
# API GDI de Windows
# ============================================================

gdi32 = ctypes.windll.gdi32

gdi32.CreateRectRgn.argtypes = [
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
]

gdi32.CreateRectRgn.restype = wintypes.HRGN


# ============================================================
# Vérifie si une fenêtre est "cloaked"
# ============================================================

def est_cloaked(hwnd):
    try:
        dwmapi = ctypes.windll.dwmapi
        cloaked = wintypes.DWORD()

        res = dwmapi.DwmGetWindowAttribute(
            hwnd,
            DWMWA_CLOAKED,
            ctypes.byref(cloaked),
            ctypes.sizeof(cloaked)
        )

        if res == 0:
            return cloaked.value != 0

    except Exception:
        pass

    return False


# ============================================================
# Vérifie si une fenêtre est valide
# ============================================================

def fenetre_valide(hwnd):

    if not win32gui.IsWindowVisible(hwnd):
        return False

    if win32gui.IsIconic(hwnd):
        return False

    if est_cloaked(hwnd):
        return False

    rect = win32gui.GetWindowRect(hwnd)

    largeur = rect[2] - rect[0]
    hauteur = rect[3] - rect[1]

    if largeur <= 0 or hauteur <= 0:
        return False

    if rect[0] <= -30000 or rect[1] <= -30000:
        return False

    return True


# ============================================================
# Vérifie si une fenêtre est totalement occultée
# ============================================================

def est_totalement_occultee(rect, occulteurs_au_dessus):

    region = gdi32.CreateRectRgn(
        rect[0],
        rect[1],
        rect[2],
        rect[3]
    )

    if not region:
        return False

    for orect in occulteurs_au_dessus:

        oregion = gdi32.CreateRectRgn(
            orect[0],
            orect[1],
            orect[2],
            orect[3]
        )

        if not oregion:
            continue

        resultat = win32gui.CombineRgn(
            region,
            region,
            oregion,
            win32con.RGN_DIFF
        )

        win32gui.DeleteObject(oregion)

        if resultat == win32con.NULLREGION:
            win32gui.DeleteObject(region)
            return True

    win32gui.DeleteObject(region)

    return False


# ============================================================
# Liste les applications réellement visibles
# ============================================================

def lister_applications():

    z_order = []

    def callback_enum(hwnd, resultats):

        if fenetre_valide(hwnd):
            resultats.append(hwnd)

        return True

    win32gui.EnumWindows(callback_enum, z_order)

    applications = []

    for i, hwnd in enumerate(z_order):

        titre = win32gui.GetWindowText(hwnd)

        # Ignorer les fenêtres sans titre
        if not titre.strip():
            continue

        rect = win32gui.GetWindowRect(hwnd)

        # Fenêtres situées au-dessus
        occulteurs_au_dessus = [
            win32gui.GetWindowRect(h)
            for h in z_order[:i]
        ]

        # Si complètement cachée, on ignore
        if est_totalement_occultee(
            rect,
            occulteurs_au_dessus
        ):
            continue

        # Récupération du processus
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            process = psutil.Process(pid)

            nom_app = process.name()

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied
        ):
            nom_app = "Inconnu"

        # Ajouter uniquement application + titre
        applications.append(json.dumps({
            "application": nom_app,
            "titre": titre
        }))

    return {
        "applications": applications
    }


# ============================================================
# Programme principal
# ============================================================

if __name__ == "__main__":

    resultat = lister_applications()

    print(
        json.dumps(
            resultat,
            ensure_ascii=False,
            indent=4
        )
    )