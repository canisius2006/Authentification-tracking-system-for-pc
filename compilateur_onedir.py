import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import threading
import sys

"""Ce script permet de compiler le fichier main avec Nuitka."""


# ============================================================
# CONFIGURATION
# ============================================================

root = tk.Tk()
root.title("Build Nuitka")
root.geometry("600x300")
root.resizable(False, False)


# ============================================================
# VARIABLES
# ============================================================

ico_path = tk.StringVar()
main_path = tk.StringVar()
status = tk.StringVar(value="Prêt")


# ============================================================
# SÉLECTION ICÔNE
# ============================================================

def choisir_icone():

    fichier = filedialog.askopenfilename(
        title="Choisir l'icône",
        filetypes=[
            ("Icône Windows", "*.ico"),
            ("Tous les fichiers", "*.*")
        ]
    )

    if fichier:
        ico_path.set(fichier)


# ============================================================
# SÉLECTION MAIN.PY
# ============================================================

def choisir_main():

    fichier = filedialog.askopenfilename(
        title="Choisir le fichier Python principal",
        filetypes=[
            ("Fichiers Python", "*.py"),
            ("Tous les fichiers", "*.*")
        ]
    )

    if fichier:
        main_path.set(fichier)


# ============================================================
# LANCEMENT NUITKA
# ============================================================

def compiler():

    ico = ico_path.get()
    main = main_path.get()

    if not ico:
        messagebox.showerror(
            "Erreur",
            "Veuillez sélectionner une icône .ico."
        )
        return

    if not main:
        messagebox.showerror(
            "Erreur",
            "Veuillez sélectionner le fichier Python principal."
        )
        return

    if not os.path.isfile(ico):
        messagebox.showerror(
            "Erreur",
            f"Icône introuvable :\n{ico}"
        )
        return

    if not os.path.isfile(main):
        messagebox.showerror(
            "Erreur",
            f"Fichier Python introuvable :\n{main}"
        )
        return

    # ========================================================
    # PYTHON UTILISÉ
    # ========================================================

    # sys.executable correspond exactement au Python
    # qui exécute actuellement ce script.
    python_exe = sys.executable

    print("Python utilisé :", python_exe)

    # ========================================================
    # CONSTRUCTION DE LA COMMANDE
    # ========================================================

    commande = [
        python_exe,
        "-m",
        "nuitka",
        "--onedir",
        "--enable-plugin=tk-inter",
        "--windows-console-mode=disable",
        f"--windows-icon-from-ico={ico}",
        main
    ]

    status.set(
        "Compilation en cours..."
    )

    bouton_compiler.config(
        state="disabled"
    )

    # ========================================================
    # LANCEMENT DANS UN THREAD
    # ========================================================

    thread = threading.Thread(
        target=lancer_nuitka,
        args=(
            commande,
            os.path.dirname(main)
        ),
        daemon=True
    )

    thread.start()


# ============================================================
# NUITKA
# ============================================================

def lancer_nuitka(commande, dossier):

    try:

        resultat = subprocess.run(
            commande,
            cwd=dossier,
            capture_output=True,
            text=True
        )

        if resultat.returncode == 0:

            root.after(
                0,
                compilation_reussie,
                resultat.stdout
            )

        else:

            root.after(
                0,
                compilation_echouee,
                resultat.stderr,
                resultat.stdout
            )

    except Exception as e:

        root.after(
            0,
            compilation_erreur,
            str(e)
        )


# ============================================================
# RÉSULTATS
# ============================================================

def compilation_reussie(sortie):

    status.set(
        "Compilation terminée."
    )

    bouton_compiler.config(
        state="normal"
    )

    messagebox.showinfo(
        "Nuitka",
        "La compilation s'est terminée avec succès."
    )


def compilation_echouee(erreur, sortie):

    status.set(
        "Erreur lors de la compilation."
    )

    bouton_compiler.config(
        state="normal"
    )

    messagebox.showerror(
        "Erreur Nuitka",
        f"La compilation a échoué.\n\n"
        f"{erreur}\n\n"
        f"Sortie :\n{sortie}"
    )


def compilation_erreur(erreur):

    status.set(
        "Erreur."
    )

    bouton_compiler.config(
        state="normal"
    )

    messagebox.showerror(
        "Erreur",
        erreur
    )


# ============================================================
# INTERFACE
# ============================================================

titre = tk.Label(
    root,
    text="Compilateur Nuitka",
    font=("Arial", 18, "bold")
)

titre.pack(
    pady=20
)


# ------------------------------------------------------------
# ICÔNE
# ------------------------------------------------------------

frame_ico = tk.Frame(root)

frame_ico.pack(
    fill="x",
    padx=20,
    pady=5
)

tk.Label(
    frame_ico,
    text="Icône :",
    width=12,
    anchor="w"
).pack(
    side="left"
)

tk.Entry(
    frame_ico,
    textvariable=ico_path
).pack(
    side="left",
    fill="x",
    expand=True
)

tk.Button(
    frame_ico,
    text="Parcourir",
    command=choisir_icone
).pack(
    side="left",
    padx=5
)


# ------------------------------------------------------------
# MAIN.PY
# ------------------------------------------------------------

frame_main = tk.Frame(root)

frame_main.pack(
    fill="x",
    padx=20,
    pady=5
)

tk.Label(
    frame_main,
    text="Main.py :",
    width=12,
    anchor="w"
).pack(
    side="left"
)

tk.Entry(
    frame_main,
    textvariable=main_path
).pack(
    side="left",
    fill="x",
    expand=True
)

tk.Button(
    frame_main,
    text="Parcourir",
    command=choisir_main
).pack(
    side="left",
    padx=5
)


# ------------------------------------------------------------
# BOUTON COMPILER
# ------------------------------------------------------------

bouton_compiler = tk.Button(
    root,
    text="COMPILER AVEC NUITKA",
    command=compiler,
    font=("Arial", 11, "bold"),
    height=2
)

bouton_compiler.pack(
    pady=25
)


# ------------------------------------------------------------
# STATUS
# ------------------------------------------------------------

tk.Label(
    root,
    textvariable=status
).pack()


# ============================================================
# LANCEMENT
# ============================================================

root.mainloop()