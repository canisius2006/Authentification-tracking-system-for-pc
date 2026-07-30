"""Application d'authentification (connexion + inscription multi-étapes).

Interface construite avec customtkinter, communiquant avec une API REST
(JWT) via des requêtes HTTP exécutées dans un thread séparé pour ne
jamais bloquer l'interface graphique.

La photo de profil est prise directement avec la webcam, à l'intérieur
même de la fenêtre principale (pas de sélection de fichier, pas de
fenêtre séparée pour la caméra : tout se passe dans une seule et même
fenêtre, du début à la fin de l'inscription). Elle est conservée
uniquement en mémoire (objet PIL.Image) et n'est jamais écrite sur
disque par l'application : elle est encodée en base64 au moment de
l'envoi du formulaire d'inscription.

Interface : grande, simple et lisible (gros textes, gros boutons,
gros champs) pour rester confortable même pour de jeunes utilisateurs.

Correction importante : les boutons "Précédent" / "Suivant" (et le lien
de connexion) étaient parfois écrasés/rétrécis quand le contenu d'une
étape était haut (ex. étape photo). Toute la page d'inscription (titre,
progression, contenu de l'étape, messages ET boutons) est maintenant
placée dans un unique CTkScrollableFrame qui défile en bloc si besoin :
les boutons gardent toujours leur taille normale, c'est la fenêtre qui
défile pour les révéler, au lieu qu'un scrollbar soit limité à une
sous-frame interne.
"""

import json
import re
import threading
import urllib.error
import urllib.request
from io import BytesIO
import base64

import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageOps

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/"
REGISTER_ENDPOINT = "/inscription"
LOGIN_ENDPOINT = "/token/"

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^[+]?\d{6,15}$")

# Taille de la zone d'aperçu photo : sert à la fois pour le flux caméra en
# direct et pour la photo capturée, afin que la mise en page ne bouge pas
# quand on passe de l'un à l'autre.
PHOTO_PREVIEW_SIZE = (440, 330)

# ---------------------------------------------------------------------------
# Palette : une seule couleur d'accent (indigo), utilisée pour toutes les
# actions principales. Les autres teintes (émeraude, rose) sont réservées
# exclusivement aux états sémantiques (succès / erreur), jamais à la
# décoration. C'est ce qui donne une hiérarchie lisible plutôt qu'un arc-en-ciel
# de boutons de couleurs différentes sans logique.
# ---------------------------------------------------------------------------
COLORS = {
    "bg": "#12151d",
    "surface": "#191d28",
    "surface_alt": "#20263443",
    "surface_raised": "#232a3a",
    "border": "#2b3245",
    "text": "#eef1f7",
    "text_muted": "#8890a3",
    "primary": "#5865e8",
    "primary_hover": "#4650c4",
    "primary_text_on": "#ffffff",
    "success": "#33b17a",
    "success_soft": "#1c2e28",
    "danger": "#e2596b",
    "danger_soft": "#2e1e22",
}

FONT_FAMILY = "Segoe UI"


def font(size, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


# ---------------------------------------------------------------------------
# Fabriques de boutons : trois niveaux de hiérarchie utilisés PARTOUT dans
# l'application, pour que "Suivant" et "Se connecter" se ressemblent, que
# "Précédent" ait toujours la même allure secondaire, etc.
#
# Les tailles ont été nettement agrandies (hauteur, police, coins arrondis)
# pour une interface plus confortable, plus "grosse" et plus facile à
# comprendre d'un coup d'œil, y compris pour de jeunes utilisateurs.
# ---------------------------------------------------------------------------
def primary_button(parent, text, command, width=260, height=64):
    return ctk.CTkButton(
        parent, text=text, command=command, width=width, height=height,
        corner_radius=16, font=font(18, "bold"),
        fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
        text_color=COLORS["primary_text_on"],
    )


def secondary_button(parent, text, command, width=220, height=64):
    return ctk.CTkButton(
        parent, text=text, command=command, width=width, height=height,
        corner_radius=16, font=font(17, "bold"),
        fg_color="transparent", hover_color=COLORS["surface_raised"],
        text_color=COLORS["text"], border_width=2, border_color=COLORS["border"],
    )


def ghost_button(parent, text, command, width=300, height=46):
    return ctk.CTkButton(
        parent, text=text, command=command, width=width, height=height,
        corner_radius=12, font=font(14, "bold"),
        fg_color="transparent", hover_color=COLORS["surface_raised"],
        text_color=COLORS["text_muted"],
    )


def danger_button(parent, text, command, width=200, height=44):
    return ctk.CTkButton(
        parent, text=text, command=command, width=width, height=height,
        corner_radius=12, font=font(14, "bold"),
        fg_color="transparent", hover_color=COLORS["danger_soft"],
        text_color=COLORS["danger"], border_width=2, border_color=COLORS["danger"],
    )


def icon_toggle_button(parent, command, height=54, width=58):
    """Gros bouton carré pour afficher/masquer un mot de passe (icône seule,
    collé au champ, plutôt qu'un gros bouton texte séparé)."""
    return ctk.CTkButton(
        parent, text="\U0001F441", command=command, width=width, height=height,
        corner_radius=14, font=font(20),
        fg_color=COLORS["surface_raised"], hover_color=COLORS["border"],
        text_color=COLORS["text_muted"],
    )


def field_label(frame, text):
    ctk.CTkLabel(
        frame, text=text, font=font(16, "bold"), text_color=COLORS["text"], anchor="w"
    ).pack(padx=32, pady=(6, 8), fill="x")


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Authentification JWT")
        self.geometry("1150x860")
        self.minsize(1000, 700)
        self.configure(fg_color=COLORS["bg"])

        self.api_base_url_var = ctk.StringVar(value=DEFAULT_API_BASE_URL)
        self.api_base_url = self.api_base_url_var.get()
        self.access_token = None
        self.refresh_token = None

        self._build_header()
        self._build_pages()
        self.show_page("login")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """S'assure que la webcam est bien libérée avant de fermer
        l'application (au cas où l'utilisateur quitte pendant que la
        caméra de l'étape photo est active)."""
        register_page = self.pages.get("register")
        if register_page is not None:
            register_page._stop_camera_preview()
        self.destroy()

    # ------------------------------------------------------------------
    # En-tête : onglets avec indicateur (au lieu de deux boutons pleins de
    # couleurs différentes qui se battent visuellement).
    # ------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0)
        header.pack(side="top", fill="x")

        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.grid(row=0, column=0, padx=32, pady=(26, 20), sticky="w")

        ctk.CTkLabel(
            title_block, text="Plateforme d'authentification",
            font=font(26, "bold"), text_color=COLORS["text"], anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_block, text="Connexion et inscription sécurisées via JWT",
            font=font(14), text_color=COLORS["text_muted"], anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        tab_wrap = ctk.CTkFrame(header, fg_color="transparent")
        tab_wrap.grid(row=0, column=1, padx=32, pady=(26, 0), sticky="e")

        tab_width = 180
        self.login_nav = ctk.CTkButton(
            tab_wrap, text="\U0001F511  Connexion", width=tab_width, height=46,
            corner_radius=0, font=font(15, "bold"),
            fg_color="transparent", hover_color=COLORS["surface_raised"],
            command=lambda: self.show_page("login"),
        )
        self.login_nav.grid(row=0, column=0)

        self.register_nav = ctk.CTkButton(
            tab_wrap, text="\U0001F4DD  Inscription", width=tab_width, height=46,
            corner_radius=0, font=font(15, "bold"),
            fg_color="transparent", hover_color=COLORS["surface_raised"],
            command=lambda: self.show_page("register"),
        )
        self.register_nav.grid(row=0, column=1)

        self.tab_indicator = ctk.CTkFrame(tab_wrap, fg_color=COLORS["primary"], height=4, width=tab_width, corner_radius=0)
        self.tab_indicator.grid(row=1, column=0, sticky="w")

        header.grid_columnconfigure(0, weight=1)

        server_row = ctk.CTkFrame(header, fg_color="transparent")
        # server_row.grid(row=1, column=0, columnspan=2, padx=32, pady=(6, 20), sticky="we")
        # server_row.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(
            server_row, textvariable=self.api_base_url_var, corner_radius=10,
            placeholder_text="URL du serveur API", height=40, font=font(13),
        )#.grid(row=0, column=0, padx=(0, 10), sticky="we")

        ctk.CTkButton(
            server_row, text="Appliquer", command=self.update_api_base_url,
            width=120, height=40, corner_radius=10, font=font(13, "bold"),
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            text_color=COLORS["primary_text_on"],
        )#.grid(row=0, column=1)

    def _build_pages(self):
        container = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        container.pack(expand=True, fill="both", padx=32, pady=(0, 32))

        self.pages = {
            "login": LoginPage(container, self),
            "register": RegisterPage(container, self),
        }
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

    def show_page(self, page_name):
        for page in self.pages.values():
            page.lower()
        target = self.pages.get(page_name)
        if target:
            target.lift()
            self._update_nav_buttons(page_name)

    def _update_nav_buttons(self, page_name):
        active_color = COLORS["text"]
        inactive_color = COLORS["text_muted"]
        self.login_nav.configure(text_color=active_color if page_name == "login" else inactive_color)
        self.register_nav.configure(text_color=active_color if page_name == "register" else inactive_color)
        self.tab_indicator.grid_configure(column=0 if page_name == "login" else 1)

    # ------------------------------------------------------------------
    # Réseau
    # ------------------------------------------------------------------
    def store_tokens(self, response_data):
        self.access_token = (
            response_data.get("access")
            or response_data.get("access_token")
            or response_data.get("access_key")
        )
        self.refresh_token = (
            response_data.get("refresh")
            or response_data.get("refresh_token")
            or response_data.get("refresh_key")
        )

    def update_api_base_url(self):
        self.api_base_url = self.api_base_url_var.get().strip()
        if not self.api_base_url:
            self.api_base_url = DEFAULT_API_BASE_URL
        self.api_base_url_var.set(self.api_base_url)

    def _format_error(self, raw_error):
        if isinstance(raw_error, urllib.error.HTTPError):
            try:
                body = raw_error.read().decode("utf-8")
                parsed = json.loads(body)
                return parsed.get("detail") or parsed.get("message") or body
            except (json.JSONDecodeError, UnicodeDecodeError):
                return f"HTTP {raw_error.code} : {raw_error.reason}"
        if isinstance(raw_error, urllib.error.URLError):
            return f"Impossible de contacter le serveur : {raw_error.reason}"
        return str(raw_error)

    def perform_request(self, endpoint, payload):
        if not self.api_base_url:
            raise RuntimeError("Veuillez configurer l'URL du serveur API via le champ en haut.")

        request_url = f"{self.api_base_url.rstrip('/')}{endpoint}"
        request_data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            request_url, data=request_data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            response_text = response.read().decode("utf-8")
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                return {}

    def _send_request(self, endpoint, payload, callback):
        def worker():
            try:
                result = self.perform_request(endpoint, payload)
                self.after(0, lambda: callback(success=True, result=result))
            except Exception as error:
                self.after(0, lambda: callback(success=False, error=error))

        threading.Thread(target=worker, daemon=True).start()

    def send_login_request(self, payload, callback):
        self._send_request(LOGIN_ENDPOINT, payload, callback)

    def send_register_request(self, payload, callback):
        self._send_request(REGISTER_ENDPOINT, payload, callback)


class LoginPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.controller = controller
        self._request_in_flight = False

        ctk.CTkLabel(self, text="Bon retour \U0001F44B", font=font(32, "bold"), text_color=COLORS["text"]).pack(pady=(48, 10))
        ctk.CTkLabel(
            self,
            text=(
                "Connectez-vous avec votre matricule, téléphone, email ou nom d'utilisateur.\n"
                "Un jeton d'accès et un jeton de rafraîchissement vous seront délivrés."
            ),
            font=font(15), text_color=COLORS["text_muted"], wraplength=760, justify="center",
        ).pack(pady=(0, 32))

        form = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=22, border_width=1, border_color=COLORS["border"])
        form.pack(padx=32, pady=10, fill="x")

        field_label(form, "Identifiant")
        self.username_entry = ctk.CTkEntry(
            form, placeholder_text="Matricule, email, téléphone ou nom d'utilisateur",
            height=54, font=font(15), corner_radius=12,
        )
        self.username_entry.pack(padx=32, pady=(0, 18), fill="x")

        field_label(form, "Mot de passe")
        password_row = ctk.CTkFrame(form, fg_color="transparent")
        password_row.pack(padx=32, pady=(0, 10), fill="x")
        password_row.grid_columnconfigure(0, weight=1)

        self.password_entry = ctk.CTkEntry(password_row, placeholder_text="Mot de passe", height=54, font=font(15), show="*", corner_radius=12)
        self.password_entry.grid(row=0, column=0, sticky="we", padx=(0, 10))
        self.password_entry.bind("<Return>", lambda _e: self.login())

        self.password_toggle = icon_toggle_button(password_row, self._toggle_password)
        self.password_toggle.grid(row=0, column=1)

        self.status_label = ctk.CTkLabel(form, text="", text_color=COLORS["danger"], font=font(15), wraplength=720, justify="center")
        self.status_label.pack(padx=32, pady=(6, 2))

        self.result_label = ctk.CTkLabel(form, text="", text_color=COLORS["text_muted"], font=font(13), wraplength=720, justify="center")
        self.result_label.pack(padx=32, pady=(0, 10))

        button_row = ctk.CTkFrame(form, fg_color="transparent")
        button_row.pack(padx=32, pady=(6, 32))

        self.login_button = primary_button(button_row, "\U0001F511  Se connecter", self.login, width=240)
        self.login_button.pack(side="left", padx=(0, 14))
        secondary_button(button_row, "\U00002728  Créer un compte", lambda: controller.show_page("register"), width=240).pack(side="left")

        self.server_info = ctk.CTkLabel(
            self, text=f"Serveur API configuré : {controller.api_base_url}",
            text_color=COLORS["text_muted"], font=font(12),
        )
        self.server_info.pack(pady=(16, 0))

    def _toggle_password(self):
        if self.password_entry.cget("show") == "*":
            self.password_entry.configure(show="")
            self.password_toggle.configure(text="\U0001F648")
        else:
            self.password_entry.configure(show="*")
            self.password_toggle.configure(text="\U0001F441")

    def login(self):
        if self._request_in_flight:
            return
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            self.status_label.configure(text="\U000026A0 Veuillez renseigner tous les champs.", text_color=COLORS["danger"])
            return

        self._set_loading(True)
        self.status_label.configure(text="Connexion en cours...", text_color=COLORS["text_muted"])
        self.result_label.configure(text="")
        self.controller.send_login_request({"username": username, "password": password}, self.login_callback)

    def _set_loading(self, loading):
        self._request_in_flight = loading
        self.login_button.configure(state="disabled" if loading else "normal")

    def login_callback(self, success, result=None, error=None):
        self._set_loading(False)
        if not success:
            self.status_label.configure(text="\U0000274C " + self.controller._format_error(error), text_color=COLORS["danger"])
            return

        self.controller.store_tokens(result)
        access = self.controller.access_token or "non fourni"
        refresh = self.controller.refresh_token or "non fourni"
        self.status_label.configure(text="\U00002705 Connexion réussie.", text_color=COLORS["success"])
        self.result_label.configure(text=f"Jeton d'accès : {access}\nJeton de rafraîchissement : {refresh}")


class RegisterPage(ctk.CTkFrame):
    STEP_TITLES = [
        "Informations personnelles",
        "Contact et photo de profil",
        "Mot de passe",
        "Nom d'utilisateur",
    ]

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.controller = controller
        self.current_step = 0
        self._request_in_flight = False
        # Verrou anti-double-clic : évite que deux clics rapprochés sur
        # "Suivant"/"Précédent" ne déclenchent deux changements d'étape
        # d'affilée (ce qui ferait sauter une étape, ex. celle de la photo).
        self._navigating = False

        # Photo de profil : gardée uniquement en mémoire (jamais écrite sur
        # disque par l'application). self.profile_photo_image est l'objet
        # PIL.Image source ; self._profile_ctk_image est la miniature affichée
        # (référence conservée pour éviter que Tk ne la libère trop tôt).
        self.profile_photo_image = None
        self._profile_ctk_image = None

        # État du flux caméra intégré (pas de fenêtre séparée : la caméra
        # s'affiche directement dans l'étape "photo" de cette même page).
        self._cv2 = None
        self.camera_capture = None
        self._camera_active = False
        self._camera_after_id = None

        # --------------------------------------------------------------
        # IMPORTANT (correction du bug d'affichage) :
        # Toute la page (titre, barre de progression, contenu de l'étape,
        # messages, ET boutons de navigation) est placée à l'intérieur d'un
        # seul CTkScrollableFrame qui occupe toute la fenêtre. C'est ce
        # scrollable-là qui défile, et lui seul : on n'a plus de scrollbar
        # "coincé" dans une sous-frame. Les boutons ne sont plus ancrés en
        # side="bottom" ; ils sont simplement les derniers éléments empilés
        # (side="top", dans l'ordre normal), ce qui évite qu'ils ne se
        # retrouvent écrasés/rétrécis quand un autre élément (ex. l'étape
        # photo) grandit : ils gardent toujours leur taille normale, et
        # c'est la page entière qui défile pour les révéler si besoin.
        # --------------------------------------------------------------
        self.page_scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.page_scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(self.page_scroll, text="Créer un compte \U00002728", font=font(30, "bold"), text_color=COLORS["text"]).pack(pady=(28, 8))
        ctk.CTkLabel(
            self.page_scroll, text="Avancez étape par étape pour créer votre compte.",
            font=font(15), text_color=COLORS["text_muted"], wraplength=760, justify="center",
        ).pack(pady=(0, 16))

        self.progress_bar = ctk.CTkProgressBar(
            self.page_scroll, width=760, height=10, progress_color=COLORS["primary"], fg_color=COLORS["border"], corner_radius=5,
        )
        self.progress_bar.pack(pady=(0, 8))
        self.progress_bar.set(0)

        self.step_label = ctk.CTkLabel(self.page_scroll, text="", font=font(14, "bold"), text_color=COLORS["text_muted"])
        self.step_label.pack(pady=(0, 14))

        # Le contenu de l'étape n'a plus besoin de son propre scrollbar
        # (c'est la page entière qui défile désormais) : simple CTkFrame.
        self.steps_container = ctk.CTkFrame(
            self.page_scroll, fg_color=COLORS["surface"], corner_radius=22,
            border_width=1, border_color=COLORS["border"],
        )
        self.step_frames = self._build_steps()
        self.steps_container.pack(side="top", padx=32, pady=(0, 6), fill="x")

        self.status_label = ctk.CTkLabel(self.page_scroll, text="", text_color=COLORS["danger"], font=font(15), wraplength=760, justify="center")
        self.status_label.pack(side="top", pady=(10, 0))

        self.result_label = ctk.CTkLabel(self.page_scroll, text="", text_color=COLORS["text_muted"], font=font(13), wraplength=760, justify="center")
        self.result_label.pack(side="top", pady=(2, 0))

        self.navigation_row = ctk.CTkFrame(self.page_scroll, fg_color="transparent")
        self.navigation_row.pack(side="top", pady=(12, 6))

        self.back_button = secondary_button(self.navigation_row, "\U00002B05  Précédent", self.previous_step, width=190)
        self.back_button.pack(side="left", padx=(0, 14))

        self.next_button = primary_button(self.navigation_row, "Suivant  \U000027A1", self.next_step, width=220)
        self.next_button.pack(side="left")

        ghost_button(
            self.page_scroll, "\U0001F511  Déjà un compte ? Se connecter",
            self._go_to_login, width=340,
        ).pack(side="top", pady=(6, 14))

        self.show_step(0)

    # ------------------------------------------------------------------
    # Construction des étapes
    # ------------------------------------------------------------------
    def _build_steps(self):
        return [self._create_step_one(), self._create_step_two(), self._create_step_three(), self._create_step_four()]

    def _step_header(self, frame, index):
        ctk.CTkLabel(
            frame, text=f"Étape {index + 1} sur {len(self.STEP_TITLES)} \u00B7 {self.STEP_TITLES[index]}",
            font=font(20, "bold"), text_color=COLORS["text"],
        ).pack(pady=(28, 20))

    def _create_step_one(self):
        frame = ctk.CTkFrame(self.steps_container, fg_color="transparent")
        self._step_header(frame, 0)

        field_label(frame, "Prénom")
        self.first_name_entry = ctk.CTkEntry(frame, placeholder_text="Prénom", height=54, font=font(15), corner_radius=12)
        self.first_name_entry.pack(padx=32, pady=(0, 14), fill="x")

        field_label(frame, "Nom")
        self.last_name_entry = ctk.CTkEntry(frame, placeholder_text="Nom", height=54, font=font(15), corner_radius=12)
        self.last_name_entry.pack(padx=32, pady=(0, 14), fill="x")

        field_label(frame, "Sexe")
        self.gender_var = ctk.StringVar(value="H")
        radio_frame = ctk.CTkFrame(frame, fg_color="transparent")
        radio_frame.pack(padx=32, pady=(0, 28), fill="x")
        ctk.CTkRadioButton(
            radio_frame, text="Homme", variable=self.gender_var, value="H", font=font(15),
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            radiobutton_width=24, radiobutton_height=24,
        ).pack(side="left", padx=(0, 36))
        ctk.CTkRadioButton(
            radio_frame, text="Femme", variable=self.gender_var, value="F", font=font(15),
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            radiobutton_width=24, radiobutton_height=24,
        ).pack(side="left")

        return frame

    def _create_step_two(self):
        frame = ctk.CTkFrame(self.steps_container, fg_color="transparent")
        self._step_header(frame, 1)

        field_label(frame, "Email (facultatif)")
        self.email_entry = ctk.CTkEntry(frame, placeholder_text="nom@exemple.com", height=54, font=font(15), corner_radius=12)
        self.email_entry.pack(padx=32, pady=(0, 14), fill="x")

        field_label(frame, "Téléphone (facultatif)")
        self.phone_entry = ctk.CTkEntry(frame, placeholder_text="+229 XX XX XX XX", height=54, font=font(15), corner_radius=12)
        self.phone_entry.pack(padx=32, pady=(0, 18), fill="x")

        field_label(frame, "Photo de profil (facultatif)")

        # Carte caméra : tout se passe ici, dans la même fenêtre. Pas de
        # sélection de fichier, pas de fenêtre séparée pour la caméra.
        camera_card = ctk.CTkFrame(
            frame, fg_color=COLORS["surface_raised"], corner_radius=20,
            border_width=1, border_color=COLORS["border"],
        )
        camera_card.pack(padx=32, pady=(0, 18), fill="x")

        self.photo_preview_label = ctk.CTkLabel(
            camera_card, text="Initialisation de la caméra...",
            width=PHOTO_PREVIEW_SIZE[0], height=PHOTO_PREVIEW_SIZE[1],
            fg_color=COLORS["surface"], corner_radius=18,
            text_color=COLORS["text_muted"], font=font(14), wraplength=PHOTO_PREVIEW_SIZE[0] - 40,
        )
        self.photo_preview_label.pack(padx=22, pady=(22, 10))

        self.camera_status_label = ctk.CTkLabel(camera_card, text="", font=font(13), text_color=COLORS["text_muted"])
        self.camera_status_label.pack(pady=(0, 6))

        # Bouton visible tant qu'aucune photo n'a été prise.
        self.capture_photo_button = primary_button(
            camera_card, "\U0001F4F8  Prendre la photo", self._capture_photo_from_camera, width=300, height=58,
        )
        self.capture_photo_button.pack(pady=(0, 22))

        # Bouton visible uniquement après la capture (pack géré dynamiquement).
        self.retake_photo_button = secondary_button(
            camera_card, "\U0001F504  Reprendre la photo", self._retake_photo, width=300, height=54,
        )

        ctk.CTkLabel(
            frame,
            text="\U0001F512 La photo n'est jamais enregistrée sur votre disque : elle reste en mémoire et n'est envoyée qu'à la création du compte.",
            font=font(12), text_color=COLORS["text_muted"], wraplength=680, justify="left",
        ).pack(padx=32, pady=(0, 10), anchor="w")

        return frame

    def _create_step_three(self):
        frame = ctk.CTkFrame(self.steps_container, fg_color="transparent")
        self._step_header(frame, 2)

        field_label(frame, "Mot de passe")
        password_row = ctk.CTkFrame(frame, fg_color="transparent")
        password_row.pack(padx=32, pady=(0, 14), fill="x")
        password_row.grid_columnconfigure(0, weight=1)
        self.password_entry = ctk.CTkEntry(password_row, placeholder_text="Au moins 8 caractères", height=54, font=font(15), show="*", corner_radius=12)
        self.password_entry.grid(row=0, column=0, sticky="we", padx=(0, 10))
        self.password_toggle = icon_toggle_button(password_row, lambda: self._toggle_visibility(self.password_entry, self.password_toggle))
        self.password_toggle.grid(row=0, column=1)

        field_label(frame, "Confirmer le mot de passe")
        confirm_row = ctk.CTkFrame(frame, fg_color="transparent")
        confirm_row.pack(padx=32, pady=(0, 24), fill="x")
        confirm_row.grid_columnconfigure(0, weight=1)
        self.confirm_password_entry = ctk.CTkEntry(confirm_row, placeholder_text="Retapez le mot de passe", height=54, font=font(15), show="*", corner_radius=12)
        self.confirm_password_entry.grid(row=0, column=0, sticky="we", padx=(0, 10))
        self.confirm_password_toggle = icon_toggle_button(confirm_row, lambda: self._toggle_visibility(self.confirm_password_entry, self.confirm_password_toggle))
        self.confirm_password_toggle.grid(row=0, column=1)

        return frame

    def _create_step_four(self):
        frame = ctk.CTkFrame(self.steps_container, fg_color="transparent")
        self._step_header(frame, 3)

        field_label(frame, "Nom d'utilisateur")
        self.username_var = ctk.StringVar()
        self.username_var.trace_add("write", self._normalize_username)
        self.username_entry = ctk.CTkEntry(
            frame, textvariable=self.username_var, placeholder_text="Sera converti en minuscules",
            height=54, font=font(15), corner_radius=12,
        )
        self.username_entry.pack(padx=32, pady=(0, 14), fill="x")
        self.username_entry.bind("<Return>", lambda _e: self.next_step())

        ctk.CTkLabel(frame, text="Ce nom d'utilisateur doit être unique.", font=font(13), text_color=COLORS["text_muted"]).pack(padx=32, pady=(0, 24), anchor="w")

        return frame

    # ------------------------------------------------------------------
    # Mot de passe
    # ------------------------------------------------------------------
    def _toggle_visibility(self, entry, button):
        if entry.cget("show") == "*":
            entry.configure(show="")
            button.configure(text="\U0001F648")
        else:
            entry.configure(show="*")
            button.configure(text="\U0001F441")

    def _normalize_username(self, *_args):
        current_value = self.username_var.get()
        lower_value = current_value.lower()
        if current_value != lower_value:
            self.username_var.set(lower_value)

    # ------------------------------------------------------------------
    # Photo de profil — caméra intégrée directement dans la page.
    #
    # Tout se passe dans une seule fenêtre, sans sélection de fichier et
    # sans fenêtre séparée pour la caméra : la webcam démarre automatique-
    # ment quand on arrive sur l'étape "photo" (voir show_step) et sa
    # dernière image capturée reste uniquement en mémoire, jamais écrite
    # sur le disque.
    # ------------------------------------------------------------------
    def _set_preview_image(self, ctk_image, text=""):
        """Met à jour l'image affichée dans `photo_preview_label` de façon sûre.

        Le vrai bug derrière le `TclError: image "pyimageXXX" doesn't exist`
        n'est pas lié à `image=None` vs `image=""` : c'est une histoire de
        durée de vie de l'image. Chaque `CTkImage` détient en interne une
        `PhotoImage` Tk ; si plus aucune variable Python ne référence ce
        `CTkImage`, il est garbage-collecté et sa `PhotoImage` Tk sous-jacente
        est détruite côté Tcl — même si le widget `CTkLabel` pense encore
        l'utiliser. Le code appelait par endroits `self._profile_ctk_image =
        None` (ou remplaçait `_live_image_ref`) AVANT d'avoir dit au widget
        de changer d'image, ce qui pouvait détruire l'image encore
        "affichée" et faire planter le `configure()` suivant.

        Cette méthode centralise donc la mise à jour : elle garde toujours
        une référence forte sur la dernière image transmise au widget
        (`self._displayed_preview_image`), et ne la remplace/relâche
        qu'une fois le nouveau `configure()` passé avec succès. Le
        `try/except` protège en plus contre une éventuelle image déjà
        périmée créée ailleurs (défense en profondeur, sans changer le
        comportement visible)."""
        try:
            self.photo_preview_label.configure(image=ctk_image if ctk_image is not None else "", text=text)
        except tk.TclError:
            # Une image précédente référencée par le widget a été détruite
            # entre-temps (course avec le garbage collector) : on force un
            # état "vide" propre avant de réessayer une fois.
            try:
                self.photo_preview_label.configure(image="", text=text)
            except tk.TclError:
                pass
        # On garde la référence forte APRÈS le configure réussi, jamais avant.
        self._displayed_preview_image = ctk_image

    def _start_camera_preview(self):
        """Démarre le flux caméra en direct dans l'aperçu de l'étape 2.

        Ne fait rien si une photo a déjà été prise (on affiche alors cette
        photo à la place) ou si le flux est déjà en cours."""
        if self.profile_photo_image is not None:
            self._show_captured_photo_state()
            return
        if self._camera_active:
            return

        if self._cv2 is None:
            try:
                import cv2
                self._cv2 = cv2
            except ImportError:
                self._show_camera_unavailable(
                    "\U0001F4F7 La prise de photo nécessite le module opencv-python.\n"
                    "Vous pouvez continuer sans photo."
                )
                return

        capture = self._cv2.VideoCapture(0)
        if not capture.isOpened():
            capture.release()
            self._show_camera_unavailable(
                "\U0001F4F7 Caméra non disponible.\nVous pouvez continuer sans photo."
            )
            return

        self.camera_capture = capture
        self._camera_active = True
        self._set_preview_image(None, text="")
        self.camera_status_label.configure(text="\U0001F3A5 Caméra active — souriez !", text_color=COLORS["text_muted"])
        self.capture_photo_button.configure(state="normal")
        self.capture_photo_button.pack(pady=(0, 22))
        self.retake_photo_button.pack_forget()
        self._update_camera_frame()

    def _update_camera_frame(self):
        if not self._camera_active or self.camera_capture is None:
            return
        ok, frame = self.camera_capture.read()
        if ok:
            # Le flip (effet miroir) est appliqué ici, une fois qu'on est
            # sûr d'avoir une frame valide : l'appliquer avant de vérifier
            # `ok` plantait (frame=None tant que la caméra "chauffe").
            frame = self._cv2.flip(frame, 1)
            rgb_frame = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(rgb_frame)
            fitted = ImageOps.fit(pil_frame, PHOTO_PREVIEW_SIZE, Image.LANCZOS)
            live_image = ctk.CTkImage(light_image=fitted, dark_image=fitted, size=PHOTO_PREVIEW_SIZE)
            self._set_preview_image(live_image, text="")
        self._camera_after_id = self.after(30, self._update_camera_frame)

    def _stop_camera_preview(self):
        """Coupe le flux caméra et libère la webcam (appelé en quittant
        l'étape photo, en changeant de page ou en fermant l'application)."""
        self._camera_active = False
        if self._camera_after_id is not None:
            try:
                self.after_cancel(self._camera_after_id)
            except Exception:
                pass
            self._camera_after_id = None
        if self.camera_capture is not None:
            self.camera_capture.release()
            self.camera_capture = None

    def _show_camera_unavailable(self, message):
        self._camera_active = False
        self._set_preview_image(None, text=message)
        self.camera_status_label.configure(text="")
        self.capture_photo_button.configure(state="disabled")
        self.capture_photo_button.pack(pady=(0, 22))
        self.retake_photo_button.pack_forget()

    def _capture_photo_from_camera(self):
        if not self._camera_active or self.camera_capture is None:
            return
        ok, frame = self.camera_capture.read()
        if not ok:
            return
        frame = self._cv2.flip(frame, 1)
        rgb_frame = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        self._set_profile_photo(Image.fromarray(rgb_frame))
        self._stop_camera_preview()
        self._show_captured_photo_state()

    def _retake_photo(self):
        self.profile_photo_image = None
        # Important : on dit d'abord au widget de ne plus utiliser
        # `_profile_ctk_image`, et on ne relâche la référence Python
        # QU'APRÈS. Faire l'inverse (comme avant) pouvait garbage-collecter
        # la CTkImage encore affichée et détruire son image Tk sous-jacente
        # avant que le widget ait fini de s'en détacher, d'où le
        # `TclError: image "pyimageXXX" doesn't exist` au configure suivant.
        self._set_preview_image(None, text="Initialisation de la caméra...")
        self._profile_ctk_image = None
        self._start_camera_preview()

    def _set_profile_photo(self, pil_image):
        self.profile_photo_image = pil_image
        thumbnail = ImageOps.fit(pil_image, PHOTO_PREVIEW_SIZE, Image.LANCZOS)
        self._profile_ctk_image = ctk.CTkImage(light_image=thumbnail, dark_image=thumbnail, size=PHOTO_PREVIEW_SIZE)

    def _show_captured_photo_state(self):
        """Affiche la photo déjà capturée (image figée) à la place du
        flux caméra, avec le bouton 'Reprendre la photo'."""
        if self._profile_ctk_image is not None:
            self._set_preview_image(self._profile_ctk_image, text="")
        self.camera_status_label.configure(text="\U00002705 Photo prise !", text_color=COLORS["success"])
        self.capture_photo_button.pack_forget()
        self.retake_photo_button.pack(pady=(0, 22))

    # ------------------------------------------------------------------
    # Navigation entre étapes
    # ------------------------------------------------------------------
    PHOTO_STEP_INDEX = 1

    def show_step(self, step_index):
        previous_step = self.current_step

        # La caméra ne doit tourner que pendant qu'on est sur l'étape photo :
        # on la coupe en la quittant, on la démarre en y entrant.
        if previous_step == self.PHOTO_STEP_INDEX and step_index != self.PHOTO_STEP_INDEX:
            self._stop_camera_preview()

        self.current_step = step_index
        for frame in self.step_frames:
            frame.pack_forget()
        self.step_frames[step_index].pack(fill="both", expand=True)

        total = len(self.step_frames)
        self.progress_bar.set((step_index + 1) / total)
        self.step_label.configure(text=f"Étape {step_index + 1} / {total} \u00B7 {self.STEP_TITLES[step_index]}")
        self.back_button.configure(state="normal" if step_index > 0 else "disabled")
        self.next_button.configure(text="\U00002705  Créer le compte" if step_index == total - 1 else "Suivant  \U000027A1")
        self.status_label.configure(text="")

        if step_index == self.PHOTO_STEP_INDEX:
            self._start_camera_preview()

        # On remonte en haut de la page à chaque changement d'étape, pour
        # que l'utilisateur voie toujours le début du formulaire (et non
        # le milieu de l'étape précédente, ni les boutons du bas).
        try:
            self.page_scroll._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _go_to_login(self):
        """Coupe la caméra si elle tourne, puis retourne à la page de
        connexion (toujours dans la même fenêtre)."""
        self._stop_camera_preview()
        self.controller.show_page("login")

    def next_step(self):
        if self._request_in_flight or self._navigating:
            return
        if self.current_step == 0 and not self._validate_step_one():
            return
        if self.current_step == 1 and not self._validate_step_two():
            return
        if self.current_step == 2 and not self._validate_step_three():
            return
        if self.current_step < len(self.step_frames) - 1:
            self.show_step(self.current_step + 1)
            self._lock_navigation()
            return
        self._submit_registration()

    def previous_step(self):
        if self.current_step > 0 and not self._request_in_flight and not self._navigating:
            self.show_step(self.current_step - 1)
            self._lock_navigation()

    def _lock_navigation(self, delay_ms=350):
        """Désactive brièvement Précédent/Suivant après un changement
        d'étape, le temps que l'interface se stabilise, pour absorber
        un double-clic impatient sans sauter d'étape."""
        self._navigating = True
        self.next_button.configure(state="disabled")
        self.back_button.configure(state="disabled")
        self.after(delay_ms, self._unlock_navigation)

    def _unlock_navigation(self):
        self._navigating = False
        if self._request_in_flight:
            return
        self.next_button.configure(state="normal")
        self.back_button.configure(state="normal" if self.current_step > 0 else "disabled")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate_step_one(self):
        if len(self.first_name_entry.get().strip()) < 2:
            self.status_label.configure(text="\U000026A0 Le prénom doit contenir au moins 2 caractères.", text_color=COLORS["danger"])
            return False
        if len(self.last_name_entry.get().strip()) < 2:
            self.status_label.configure(text="\U000026A0 Le nom doit contenir au moins 2 caractères.", text_color=COLORS["danger"])
            return False
        self.status_label.configure(text="")
        return True

    def _validate_step_two(self):
        email = self.email_entry.get().strip()
        phone = self.phone_entry.get().strip().replace(" ", "")
        if email and not EMAIL_REGEX.match(email):
            self.status_label.configure(text="\U000026A0 Veuillez entrer une adresse email valide.", text_color=COLORS["danger"])
            return False
        if phone and not PHONE_REGEX.match(phone):
            self.status_label.configure(text="\U000026A0 Veuillez entrer un numéro de téléphone valide.", text_color=COLORS["danger"])
            return False
        self.status_label.configure(text="")
        return True

    def _validate_step_three(self):
        password = self.password_entry.get().strip()
        confirm_password = self.confirm_password_entry.get().strip()
        if len(password) < 8:
            self.status_label.configure(text="\U000026A0 Le mot de passe doit contenir au moins 8 caractères.", text_color=COLORS["danger"])
            return False
        if password != confirm_password:
            self.status_label.configure(text="\U000026A0 Les mots de passe ne correspondent pas.", text_color=COLORS["danger"])
            return False
        self.status_label.configure(text="")
        return True

    def _validate_step_four(self):
        if not self.username_entry.get().strip():
            self.status_label.configure(text="\U000026A0 Le nom d'utilisateur est requis.", text_color=COLORS["danger"])
            return False
        self.status_label.configure(text="")
        return True

    # ------------------------------------------------------------------
    # Soumission
    # ------------------------------------------------------------------
    def _set_loading(self, loading):
        self._request_in_flight = loading
        self.next_button.configure(state="disabled" if loading else "normal")
        self.back_button.configure(state="disabled" if (loading or self.current_step == 0) else "normal")

    def _encode_profile_photo(self):
        """Encode la photo en mémoire en base64 pour l'inclure dans le JSON
        envoyé au serveur. Retourne une chaîne vide si aucune photo n'a été
        choisie — rien n'est jamais écrit sur le disque local."""
        if self.profile_photo_image is None:
            return ""
        buffer = BytesIO()
        self.profile_photo_image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def _submit_registration(self):
        if not self._validate_step_four():
            return

        payload = {
            "first_name": self.first_name_entry.get().strip(),
            "last_name": self.last_name_entry.get().strip(),
            "sexe": self.gender_var.get(),
            "email": self.email_entry.get().strip(),
            "telephone": self.phone_entry.get().strip(),
            "photo_de_profil": self._encode_profile_photo(),
            "username": self.username_entry.get().strip(),
            "password": self.password_entry.get().strip(),
        }
        self._set_loading(True)
        self.status_label.configure(text="Création du compte en cours...", text_color=COLORS["text_muted"])
        self.result_label.configure(text="")
        self.controller.send_register_request(payload, self.registration_callback)

    def registration_callback(self, success, result=None, error=None):
        self._set_loading(False)
        if not success:
            self.status_label.configure(text="\U0000274C " + self.controller._format_error(error), text_color=COLORS["danger"])
            return

        self.controller.store_tokens(result)
        self.status_label.configure(text="\U00002705 Inscription réussie.", text_color=COLORS["success"])
        self.result_label.configure(
            text=(
                f"Jeton d'accès : {self.controller.access_token or 'non fourni'}\n"
                f"Jeton de rafraîchissement : {self.controller.refresh_token or 'non fourni'}"
            )
        )


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()