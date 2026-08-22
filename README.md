# Authentification-tracking-system-for-pc

Système d'authentification et de suivi automatique des utilisateurs sur les postes du **CAEB Natitingou** : chaque connexion à un poste est associée à un utilisateur identifié, dont l'activité (applications/fenêtres actives) est remontée à un serveur central, analysée par une IA, et traduite en un **score de comportement sur 20 points**.

Le dépôt contient deux générations du client, qui partagent la même finalité mais pas la même architecture :

- **V1** (`client/main_v1.py`) : le client se connecte **directement à MySQL** depuis le poste. Simple inscription (nom/prénom), aucune authentification, aucun tracking.
- **V2** (`client/main_v2.py`, code actuel) : le client ne touche plus jamais MySQL. Il passe par une **API REST Django/DRF** authentifiée en JWT, et ajoute le suivi des activités, l'analyse IA et le système de score.

`main_v1.py` est conservé comme référence historique ; toute la suite de ce document décrit la V2, qui est la version active du projet.

---

## Sommaire

1. [Architecture générale](#1-architecture-générale)
2. [Client desktop (`client/`)](#2-client-desktop-client)
3. [Serveur Django (`serveur/authentification/`)](#3-serveur-django-serveurauthentification)
4. [Pipeline d'analyse IA (`analyseur.py`)](#4-pipeline-danalyse-ia-analyseurpy)
5. [Système de score](#5-système-de-score)
6. [Interface web d'administration](#6-interface-web-dadministration)
7. [Structure du dépôt](#7-structure-du-dépôt)
8. [Installation du serveur](#8-installation-du-serveur)
9. [Lancement du serveur](#9-lancement-du-serveur)
10. [Installation et lancement du client](#10-installation-et-lancement-du-client)
11. [Compilation du client avec Nuitka](#11-compilation-du-client-avec-nuitka)
12. [Lancement automatique et verrouillage du poste](#12-lancement-automatique-et-verrouillage-du-poste)
13. [Documentation de l'API](#13-documentation-de-lapi)
14. [Points de vigilance relevés dans le code](#14-points-de-vigilance-relevés-dans-le-code)
15. [Limitations connues](#15-limitations-connues)

---

## 1. Architecture générale

```text
Client CustomTkinter (poste utilisateur)
        │
        │ HTTP + JWT
        ▼
   API Django / DRF  ───────────► MySQL
        │
        │ activité active, toutes les 20 s
        ▼
     Celery (tâche verifier_activite)
        │
        ▼
  Pipeline d'analyse (analyseur.py)
        │
   ┌────┴─────┐
   │          │
activité   activité
 normale    "mauvaise"
              │
              ▼
        Bad_action créée
              │
              ▼
      score utilisateur - 1
 (puis -2 supplémentaires tous les
  6 signalements répétés de la même
  mauvaise action)
```

Le serveur sert d'intermédiaire unique entre le client et MySQL : les identifiants de base de données ne sont jamais distribués sur les postes.

---

## 2. Client desktop (`client/`)

L'application (`main_v2.py`, ~1450 lignes) est construite avec **CustomTkinter**, en plein écran, sans bordure (`overrideredirect(True)`) et toujours au premier plan (`attributes("-topmost", True)`, revérifié toutes les 200 ms par `check_focus()`).

### 2.1 Connexion / Inscription

Deux onglets partagent la même fenêtre :

- **Connexion** : identifiant (username, email, matricule ou téléphone — voir `MultifieldAuthBackend` côté serveur) + mot de passe, envoyés à `POST /api/token/`.
- **Inscription** en **5 étapes**, chacune validée avant de pouvoir avancer :
  1. Informations personnelles
  2. Contact et photo de profil
  3. Mot de passe
  4. Nom d'utilisateur
  5. Code de validation

La photo de profil est capturée **directement dans la fenêtre d'inscription** via OpenCV (pas de fenêtre séparée). Elle est gardée uniquement en mémoire (objet `PIL.Image`) puis encodée en base64 au moment de l'envoi — elle n'est jamais écrite sur le disque. La caméra est préchargée dès l'arrivée sur la page d'inscription (en arrière-plan, pendant la saisie de l'étape 1) pour que l'aperçu s'affiche instantanément à l'étape photo, et elle est explicitement relâchée à la fermeture de l'app ou en quittant la page.

Toutes les requêtes réseau sont exécutées dans des threads séparés pour ne jamais bloquer l'interface graphique.

À l'inscription, le serveur génère automatiquement :
- un **matricule** au format `AAMMUNNNCC` (année/mois sur 2 chiffres, lettre `U`, un nombre aléatoire sur 3 chiffres, une clé de contrôle mod 97 sur 2 chiffres) ;
- un **code d'activation** numérique (`random.randint(112, 9999)`, donc jusqu'à 4 chiffres), à saisir à l'étape 5 pour activer le compte (`is_active` passe à `True` et des tokens JWT sont renvoyés immédiatement).

### 2.2 Suivi (classe `Coeur`)

Une fois connecté, la classe `Coeur` prend le relais :

- crée une `Session_activite` côté serveur (`POST /api/session/`) associée au nom du poste (`socket.gethostname()`) ;
- programme trois tâches périodiques via **APScheduler** :
  - toutes les **20 secondes** : `poster_application` — récupère les fenêtres visibles (`application_monitor.lister_applications()`) et les envoie une par une à `POST /api/application/` ;
  - toutes les **minutes** : `verifier_score` — relit le score courant (`GET /api/profil/`) ;
  - toutes les **25 minutes** : rafraîchissement du token d'accès JWT.
- si le score atteint **10**, ouvre automatiquement la page profil (`/profil/<username>/`) dans le navigateur par défaut ;
- si le score atteint **0 ou moins**, ouvre la page `/extinction/` puis exécute `shutdown /s /t 30` (extinction Windows programmée dans les 30 secondes).

### 2.3 Détection de la fenêtre active — `application_monitor.py`

Contrairement à une simple lecture de `GetForegroundWindow()` (utilisée par `application_active.py`, une version plus ancienne conservée dans le dépôt mais non importée par `main_v2.py`), `application_monitor.py` énumère **toutes les fenêtres visibles** via l'API Win32 (`win32gui.EnumWindows`) et filtre :

- les fenêtres masquées, minimisées, "cloaked" (`DwmGetWindowAttribute`, utile pour les apps UWP) ;
- les fenêtres de taille nulle ou hors écran ;
- les fenêtres **totalement occultées** par d'autres fenêtres situées au-dessus dans le z-order (calcul de région GDI, `CreateRectRgn` + `CombineRgn`).

Le résultat est une liste `{"application": <nom_process.exe>, "titre": <titre_fenêtre>}` — c'est cette structure, sérialisée avec `json.dumps` côté client puis reconstruite avec `ast.literal_eval` côté serveur, qui alimente le pipeline d'analyse (voir §4).

### 2.4 Raccourcis clavier

L'application bloque `Alt+F4`, `Échap`, `Ctrl+W`, `Ctrl+Q` et intercepte la fermeture par le bouton de la fenêtre (`WM_DELETE_WINDOW`). Le raccourci d'échappement administrateur `Ctrl+Shift+B` existe dans la V1 (`main_v1.py`) mais **est actuellement commenté dans `main_v2.py`** : dans le code présent dans ce dépôt, aucun raccourci ne permet de sortir de l'application V2 sans passer par le flux normal (connexion aboutie ou extinction du poste).

---

## 3. Serveur Django (`serveur/authentification/`)

Projet Django 6 / DRF avec une seule app, `compte`.

### 3.1 Modèle utilisateur

`compte.User` étend `AbstractUser` et ajoute : `matricule` (unique), `telephone` (unique, optionnel), `email` (optionnel, unique en pratique via validation du serializer plutôt que par la contrainte du champ), `photo_de_profil`, `sexe`, `score` (défaut 20), `activation_code`, `created_at`/`updated_at`.

Trois autres modèles :
- `Session_activite` : une session = un utilisateur + un poste (`pc`) + un jour + une plage `heure_debut`/`heure_fin`.
- `Application` : une fenêtre/app suivie au sein d'une session, avec `verified` (déjà passée dans le pipeline IA) et `justification` (résultat JSON du pipeline).
- `Bad_action` : liée à une `Application`, garde le texte brut, la justification IA, et `nombre` (compteur de répétitions de la même infraction).

### 3.2 Authentification

`MultifieldAuthBackend` (backend Django personnalisé) permet de se connecter avec **username, email, matricule ou téléphone** indifféremment, sur le même champ "identifiant". L'authentification API repose sur **SimpleJWT** : access token de 30 minutes, refresh token de 1 jour, rotation + blacklist du refresh token activées.

### 3.3 Endpoints principaux (`compte/urls.py`)

| Endpoint | Méthode | Description |
|---|---|---|
| `/api/inscription` | POST | Création de compte (`is_active=False` jusqu'à validation) |
| `/api/check-user/` | GET | Vérifie la disponibilité d'un username/email/téléphone |
| `/api/validation-inscription/` | POST | Valide le code d'activation, renvoie les tokens JWT (throttlé, 3/min) |
| `/api/token/` | POST | Connexion, obtention des tokens (throttlé, 5/min) |
| `/api/token/refresh/` | POST | Rafraîchissement du token |
| `/api/profil/` et `/api/profil/<valeur>/` | GET | Profil de l'utilisateur connecté, ou par username/matricule/email/téléphone |
| `/api/session/`, `/api/application/`, `/api/bad_action/` | ViewSets DRF | Création/consultation des sessions, applications et infractions de l'utilisateur connecté |
| `/api/users/` | ViewSet | Administration complète des utilisateurs (admin uniquement) |
| `/api/liste-pending/` | GET | Comptes en attente d'activation (admin uniquement) |
| `/api/sessions/`, `/api/session-par-utilisateur/`, `/api/application-par-session/`, `/api/badaction-par-utilisateur/`, `/api/badaction-par-session/` | GET | Vues agrégées consommées par le tableau de bord web |

Documentation générée automatiquement par **drf-spectacular** :
- Schéma OpenAPI : `/api/schema/`
- Swagger UI : `/api/docs/`
- Redoc : `/api/redoc/`

### 3.4 Enregistrement d'une activité et déclenchement de l'analyse

Quand le client poste une application (`ApplicationSerializer.create`) :
1. si une `Application` du même nom existe déjà pour la session, seule son `heure_fin` est mise à jour (pas de doublon) ; sinon elle est créée ;
2. l'`heure_fin` de la session est mise à jour ;
3. la tâche Celery `verifier_activite` est déclenchée en asynchrone (`.delay(...)`) avec l'`id` de l'`Application` et le titre décodé via `ast.literal_eval`.

---

## 4. Pipeline d'analyse IA (`analyseur.py`)

Le fichier existe en deux copies dans le dépôt : `analyseur.py` (racine, exécutable seul pour des tests hors serveur) et `serveur/authentification/compte/analyseur.py` (celle réellement importée par la tâche Celery). Elles ont légèrement divergé — la version serveur est la plus à jour (prototypes d'embeddings et prompt système plus riches).

Pour chaque activité reçue, le texte `"<application> <titre>"` passe en cascade dans les étapes suivantes, chacune pouvant trancher directement (sinon on passe à la suivante) :

1. **Porte de négation** : si le texte contient des tournures comme *"arrêter"*, *"éviter de"*, *"reportage sur"*, *"documentaire sur"*..., l'activité saute directement à l'étape LLM (une recherche sur *comment arrêter de jouer* n'est pas la même chose que *jouer*).
2. **Blocklist de domaines** (`piracy.txt`, liste [Blocklist Project](https://github.com/blocklistproject/Lists) de sites de streaming/piraterie) : détection d'un nom de domaine connu dans le titre, avec correspondance par suffixe.
3. **Mots-clés de contenu non ambigus** : `trailer`, `bande-annonce`, `official music video`, `episode N`, `saison N`, `vostfr`, `gameplay`, `speedrun`, etc.
4. **Similarité d'embeddings** (modèle `bge-m3` via Ollama) : le titre nettoyé est comparé par cosinus à des phrases-prototypes "éducatif" vs "divertissement" ; le résultat n'est retenu que si l'écart entre les deux scores dépasse un seuil de marge et que le meilleur score dépasse un plancher de confiance — sinon on passe à l'étape suivante.
5. **LLM génératif** (`qwen2.5:1.5b` via Ollama) : dernier recours pour les cas ambigus ou touchés par la négation. Le modèle est interrogé **deux fois** (températures 0.0 puis 0.4) ; si les deux réponses ne concordent pas, ou si la confiance de la première réponse est trop basse (< 0,55), l'activité est classée `mauvais=None` ("incertain") plutôt que d'être devinée.

Chaque étape renvoie un dictionnaire `{title, mauvais, confiance, justification, methode}`, stocké tel quel dans `Application.justification`.

⚠️ `charger_blocklist("piracy.txt")` utilise un **chemin relatif** et avale silencieusement `FileNotFoundError` : le fichier `piracy.txt` se trouve à la racine de `serveur/`, pas dans `serveur/authentification/compte/` où s'exécute réellement le code. Selon le répertoire de travail au lancement du serveur/worker Celery, la blocklist peut donc se charger vide sans qu'aucune erreur ne soit levée — seule l'étape 2 du pipeline est affectée (les étapes 3 à 5 continuent de fonctionner normalement).

---

## 5. Système de score

Score initial : **20**. Géré par la tâche Celery `verifier_activite` (`compte/tasks.py`) :

- première activité jugée "mauvaise" pour une `Application` donnée → création d'une `Bad_action` et **-1** au score de l'utilisateur ;
- si la même infraction se reproduit sur la même `Application` (nouveaux passages du scheduler sur une fenêtre restée ouverte) → le compteur `nombre` de la `Bad_action` s'incrémente, et **tous les 6 signalements** (`nombre % 6 == 0`), une pénalité supplémentaire de **-2** est appliquée ;
- si l'activité n'est pas jugée mauvaise, aucune pénalité n'est appliquée et l'`Application` est simplement marquée `verified=True` (elle ne repasse plus dans le pipeline).

Côté client, le score est relu toutes les minutes : avertissement (ouverture de la page profil) à 10 points, extinction programmée du poste à 0 ou moins. Un administrateur peut remettre le score d'un ou plusieurs utilisateurs à 20 depuis l'admin Django (action « Remettre le score à 20 »).

---

## 6. Interface web d'administration

En plus de l'API REST, le serveur Django sert un ensemble de pages HTML (Tailwind côté front, templates dans `serveur/authentification/templates/`), toutes protégées par un contrôle `is_superuser` fait à la main dans les vues (pas de `login_required`/`permission_required` Django standard) :

| URL | Template | Rôle |
|---|---|---|
| `/dashboard/` | `dashboard.html` | Administration des utilisateurs |
| `/pending/` | `pending.html` | Inscriptions en attente d'activation |
| `/session/` | `session.html` | Historique des sessions par utilisateur |
| `/toute_session/` | `toute_session_jour.html` | Supervision de toutes les sessions du jour |
| `/session_detail/` | `session_detail.html` | Détail des applications d'une session, avec recherche/filtre |
| `/badaction/` | `badaction.html` | Liste des mauvaises actions |
| `/profil/<valeur>/` | `profil_2.html` | Profil consultable par un utilisateur (username, matricule, email ou téléphone) |
| `/guide/` | `guide.html` | Guide d'utilisation des postes |
| `/termes/` | `termes.html` | Conditions d'utilisation |
| `/extinction/` | `extinction.html` | Page affichée avant l'extinction automatique du poste |

Ces pages consomment les endpoints agrégés listés en §3.3 (`sessions-par-utilisateur`, `badaction-par-session`, etc.) en JavaScript côté client.

---

## 7. Structure du dépôt

```text
.
├── serveur/
│   ├── authentification/                 # Projet Django / API REST
│   │   ├── authentification/             # Réglages du projet
│   │   │   ├── settings.py
│   │   │   ├── celery.py
│   │   │   ├── urls.py
│   │   │   └── wsgi.py / asgi.py
│   │   ├── compte/                       # App principale
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── serializers.py
│   │   │   ├── authentication.py         # MultifieldAuthBackend
│   │   │   ├── admin.py                  # Admin Django + action "remettre score à 20"
│   │   │   ├── tasks.py                  # Tâche Celery verifier_activite
│   │   │   ├── analyseur.py              # Pipeline d'analyse IA (voir §4)
│   │   │   └── mettre_a_jour.py          # Script de maintenance : marque les vieilles sessions comme "verified"
│   │   ├── templates/                    # Tableau de bord admin + pages publiques (voir §6)
│   │   ├── static/
│   │   └── manage.py
│   └── piracy.txt                        # Blocklist utilisée par analyseur.py (attention au chemin, §4)
│
├── client/
│   ├── main_v2.py                        # Client actuel (CustomTkinter + JWT + tracking)
│   ├── main_v1.py                        # Ancien client, accès MySQL direct — référence historique
│   ├── application_monitor.py            # Détection des fenêtres visibles, utilisée par main_v2.py
│   └── application_active.py             # Détection de la seule fenêtre au premier plan (non utilisée par main_v2.py)
│
├── analyseur.py                          # Copie (légèrement désynchronisée) du pipeline, pour tests hors serveur
├── generer_matricule.py                  # Script autonome pour tester la génération de matricule
├── compilateur_main.py                   # Utilitaire graphique de compilation Nuitka (--onefile)
├── compilateur_onedir.py                 # Idem, mode Nuitka --onedir
├── lancer_serveur.py                     # Dév. : ouvre Redis/Memurai + manage.py runserver + Celery (Windows)
├── lancer_serveur_worker.py              # Prod (Windows) : Waitress + 1 worker Celery
├── lancer_serveur_worker_windows.py      # Prod (Windows) : Waitress + N workers Celery en parallèle
├── lancer_serveur_worker_linux.py        # Prod (Linux) : mêmes rôles, en processus détachés avec PID/logs
├── arreter_serveur_worker_linux.py       # Arrête proprement les processus lancés par le script Linux ci-dessus
├── requirements.txt
├── conception.md                         # Document de conception initial (certaines propositions n'ont pas été implémentées, ex. keylogging, notifications temps réel)
└── icone.ico / drawSQL-image-export-*.webp
```

---

## 8. Installation du serveur

### 8.1 Prérequis

- Python 3.x
- MySQL
- Redis (ou Memurai sous Windows)
- [Ollama](https://ollama.com), avec les modèles utilisés par le pipeline d'analyse :

```bash
ollama pull qwen2.5:1.5b
ollama pull bge-m3
```

### 8.2 Dépendances Python

```bash
cd serveur/authentification
python -m venv venv
```

Windows : `venv\Scripts\activate` — Linux/macOS : `source venv/bin/activate`, puis :

```bash
pip install -r ../../requirements.txt
```

> Le `requirements.txt` du dépôt regroupe **toutes** les dépendances du projet (serveur ET client ET outils de compilation) dans un seul fichier — il inclut par exemple `customtkinter`, `pywin32`, `opencv-contrib-python` (client), aussi bien que `django`, `celery`, `ollama` (serveur), et `nuitka`/`pyinstaller` (compilation). Sur une machine dédiée uniquement au serveur, il est possible d'alléger l'installation en n'installant que le sous-ensemble nécessaire.

### 8.3 Variables d'environnement (`.env`)

```env
SECRET_KEY=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_PORT=3306
DB_HOST=...
```

`DB_HOST` est résolu via `socket.gethostbyname()` dans `settings.py` : ce doit donc être un nom d'hôte réellement résolvable (ou une IP) au démarrage, sinon Django ne démarre pas. Le dictionnaire `DATABASES` contient aussi une entrée `sqlite` définie mais non utilisée : la connexion active (`default`) est toujours MySQL.

### 8.4 Migrations

```bash
python manage.py migrate
```

---

## 9. Lancement du serveur

Le serveur a besoin de trois composants en parallèle : Django (ou son serveur WSGI de production), Celery, et Redis. Quatre scripts à la racine du dépôt automatisent leur démarrage :

| Script | Plateforme | Usage | Détail |
|---|---|---|---|
| `lancer_serveur.py` | Windows | Développement | Détecte un `redis-cli`/`memurai-cli` fonctionnel, ouvre 3 fenêtres PowerShell : Redis/Memurai, `manage.py runserver`, Celery (`--pool=solo`) |
| `lancer_serveur_worker.py` | Windows | Production simple | 2 fenêtres PowerShell : Waitress (`0.0.0.0:8000`) + 1 worker Celery |
| `lancer_serveur_worker_windows.py` | Windows | Production, charge plus élevée | Waitress + `NB_WORKERS` workers Celery (défaut 4), chacun dans sa propre fenêtre et avec un hostname unique |
| `lancer_serveur_worker_linux.py` | Linux | Production | Mêmes rôles que la version Windows, mais en processus détachés (`start_new_session=True`), logs dans `logs/`, PID sauvegardés dans `.worker_pids` — à arrêter avec `arreter_serveur_worker_linux.py` |

Ces scripts supposent une arborescence `serveur/authentification/` avec un environnement virtuel `venv/` à la racine du projet, et lisent `DB_HOST` depuis `.env` pour construire l'adresse d'écoute de `runserver`.

⚠️ Les scripts de production font écouter Waitress sur `0.0.0.0`, c'est-à-dire sur toutes les interfaces réseau de la machine — voir §14 pour les réglages Django à vérifier avant un déploiement hors réseau de confiance.

Redis doit être lancé séparément avec les scripts de production (ce n'est que `lancer_serveur.py`, orienté développement, qui s'en charge automatiquement) :

```bash
redis-server
```

Pour suivre les tâches Celery dans un navigateur, [Flower](https://flower.readthedocs.io/) est inclus dans les dépendances :

```bash
celery -A authentification flower
```

Enfin, `compte/mettre_a_jour.py` est un script de maintenance (à exécuter manuellement ou via tâche planifiée) qui marque comme `verified` les applications des sessions des jours précédents, pour éviter qu'elles ne soient réanalysées inutilement.

---

## 10. Installation et lancement du client

Depuis le dossier `client/` :

```bash
pip install customtkinter requests pillow opencv-contrib-python apscheduler pywin32 psutil
```

```bash
python main_v2.py
```

L'URL de base de l'API (`DEFAULT_API_BASE_URL`) est actuellement construite à partir d'un nom d'hôte codé en dur (`CIA-008`, voir §14) ; un champ dans l'interface permet de la modifier au lancement, mais un déploiement multi-poste gagnerait à externaliser cette valeur dans un fichier de configuration.

L'authentification utilise **JWT** : le client obtient un `access_token` et un `refresh_token`, rafraîchit automatiquement l'access token toutes les 25 minutes, et redemande un nouveau token en cas de réponse `401`.

---

## 11. Compilation du client avec Nuitka

Le dépôt contient à la fois **Nuitka** et **PyInstaller** dans `requirements.txt`, mais les deux utilitaires graphiques fournis (`compilateur_main.py` et `compilateur_onedir.py`) sont écrits pour **Nuitka**, qui est l'outil de compilation à utiliser pour ce projet.

### 11.1 Installer Nuitka

```bash
pip install nuitka
```

Sous Windows, un compilateur C est nécessaire (Nuitka propose de télécharger automatiquement MinGW64 au premier lancement, ou un compilateur Visual Studio Build Tools existant peut être utilisé).

### 11.2 Compiler via l'utilitaire graphique du dépôt

- `compilateur_main.py` : mode **`--onefile`** (un seul exécutable autonome, plus simple à distribuer, mais qui se décompresse dans un dossier temporaire à chaque lancement).
- `compilateur_onedir.py` : mode **`--onedir`** (un dossier contenant l'exécutable et ses dépendances, démarrage plus rapide, adapté à une installation qui reste en place sur le poste).

```bash
python compilateur_main.py
```

Dans l'interface : choisir l'icône (`icone.ico`), choisir le script principal (`client/main_v2.py`), puis cliquer sur **COMPILER AVEC NUITKA**. La compilation tourne dans un thread séparé, avec le même interpréteur Python que celui qui exécute l'utilitaire (`sys.executable`).

### 11.3 Équivalent en ligne de commande

```bash
python -m nuitka --onefile --enable-plugin=tk-inter --windows-console-mode=disable --windows-icon-from-ico=icone.ico client/main_v2.py
```

(remplacer `--onefile` par `--onedir` pour l'autre mode). Options utilisées :

- `--enable-plugin=tk-inter` : requis car le client s'appuie sur CustomTkinter/Tkinter ;
- `--windows-console-mode=disable` : masque la console (application graphique) ;
- `--windows-icon-from-ico=...` : associe l'icône à l'exécutable.

Le résultat (`main_v2.exe`, ou `main_v2.dist/main_v2.exe` en mode `--onedir`) est généré dans le même dossier que le script compilé.

---

## 12. Lancement automatique et verrouillage du poste

Pour lancer l'application au démarrage de Windows, ajouter une valeur chaîne dans :

```text
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
```

avec pour valeur le chemin de l'exécutable compilé, par exemple :

```text
"C:\Program Files\CAEB\AuthCAEB.exe"
```

Cette clé nécessite des droits administrateur ; pour un déploiement sur plusieurs postes, ce réglage peut être automatisé via un script d'installation ou une stratégie de groupe (GPO).

Une fois lancée, la fenêtre est plein écran, sans bordure, toujours au premier plan, et bloque `Alt+F4`/`Échap`/`Ctrl+W`/`Ctrl+Q` (voir §2.4 pour le détail, et la remarque sur le raccourci de sortie administrateur actuellement désactivé dans la V2).

---

## 13. Documentation de l'API

Une fois le serveur Django lancé :

- Swagger : `/api/docs/`
- Redoc : `/api/redoc/`
- Schéma OpenAPI brut : `/api/schema/`

Avec le serveur local : `http://127.0.0.1:8000/api/docs/`

---

## 14. Points de vigilance relevés dans le code

Cette section documente des observations faites en lisant le code source, à vérifier/corriger avant un déploiement au-delà d'un réseau local de confiance.

### 14.1 `ALLOWED_HOSTS = ['*']`

`settings.py` accepte n'importe quel en-tête `Host` (`ALLOWED_HOSTS = ['*']`). `DEBUG` est en revanche codé en dur à `False` — les pages d'erreur détaillées de Django ne sont donc pas exposées par défaut, contrairement à une configuration `DEBUG=True`. Il reste recommandé de restreindre `ALLOWED_HOSTS` aux hôtes réellement utilisés pour tout déploiement au-delà du poste de développement.

### 14.2 Endpoint de profil non protégé

`ProfilApiView` (`GET /api/profil/<valeur>/`) ne définit pas de `permission_classes` et hérite donc du comportement par défaut de DRF (accès non authentifié). `<valeur>` peut être un `username`, `matricule`, `email` ou `telephone`, et la réponse inclut l'email, le téléphone et le score de l'utilisateur. Quiconque connaît (ou devine) un identifiant peut consulter ces informations sans se connecter. Plusieurs vues agrégées utilisées par le tableau de bord (`VoirSessionActuelleApiView`, `VoirBadactionActuelleApiView`, `VoirBadActionUtilisateurPerUserApiView`) ont le même profil : leur `permission_classes = [IsAdminUser]` est présent en commentaire mais désactivé dans le code actuel.

### 14.3 Code d'activation court, sans limitation stricte

`create_code()` génère un nombre entre 112 et 9999 (jusqu'à 4 chiffres, soit moins de 9 900 combinaisons). `ValiderInscriptionApiView` est throttlée à 3 tentatives par minute (`ScopedRateThrottle`, scope `activation`), ce qui limite le risque de force brute mais ne l'élimine pas complètement pour un attaquant patient ou multi-IP.

### 14.4 `ast.literal_eval` sur une donnée envoyée par le client

`str_to_dict()` (dans `serializers.py`) applique `ast.literal_eval()` au champ `nom` envoyé par le client. Ce n'est pas une exécution de code arbitraire (contrairement à `eval`), mais :
- toute valeur qui n'est pas une syntaxe littérale Python valide fait planter la création (exception non gérée → erreur 500) ;
- le champ `nom` stocké en base contient la représentation texte d'un dictionnaire Python plutôt qu'un nom d'application simple.
Faire transiter cette donnée en JSON (`json.dumps`/`json.loads`) plutôt qu'en syntaxe littérale Python serait plus robuste.

### 14.5 Trafic client ↔ serveur en HTTP simple

Le client construit toutes ses requêtes en `http://{HOST}/...`, sans TLS : identifiants et tokens JWT transitent en clair sur le réseau. Sur un réseau local isolé et de confiance le risque est limité ; sur un réseau partagé ou si le serveur devient un jour accessible depuis Internet, c'est une interception facile.

### 14.6 Nom d'hôte du serveur codé en dur côté client (V2) / identifiants codés en dur (V1)

`HOST = f"{socket.gethostbyname('CIA-008')}:8000"` dans `main_v2.py` force la résolution DNS/NetBIOS du nom `CIA-008` — le client n'est donc utilisable tel quel que sur un réseau où ce nom se résout, sauf à changer manuellement l'URL dans l'interface. Dans `main_v1.py` (conservé comme référence historique, non utilisé en production), les identifiants MySQL sont en clair dans le code source (`user='inscription', password='CLUBIA'`) : si ce fichier venait à être réutilisé, ces identifiants devraient être changés et déplacés vers une configuration externe.

### 14.7 Blocklist chargée avec un chemin relatif fragile

Voir §4 : `piracy.txt` est cherché avec un chemin relatif au répertoire de travail courant, qui ne correspond pas forcément à l'emplacement réel du fichier (`serveur/piracy.txt`) selon comment le serveur/worker Celery est lancé. L'erreur est avalée silencieusement, donc rien ne signale que la blocklist est vide.

### 14.8 Pas de gestion de la caméra/photo indisponible testée en dehors de Windows

`application_monitor.py` (utilisé par le tracking) dépend entièrement de l'API Win32 (`win32gui`, `win32process`, `ctypes.windll`) : le client V2 ne peut fonctionner que sous Windows.

---

## 15. Limitations connues

- `requirements.txt` mélange les dépendances serveur, client et outils de compilation dans un seul fichier (voir §8.2).
- L'URL de l'API est actuellement construite à partir d'un nom d'hôte codé en dur côté client plutôt que d'être entièrement pilotée par la configuration.
- `piracy.txt` doit être accessible depuis le répertoire de travail réel du processus qui exécute `analyseur.py` (voir §14.7).
- Le déploiement multi-poste nécessite une configuration réseau correcte entre les clients et le serveur Django (résolution du nom d'hôte, port 8000 ouvert).
- Le serveur Django doit pouvoir accéder à MySQL ; Celery doit pouvoir communiquer avec Redis ; Ollama et les modèles `qwen2.5:1.5b`/`bge-m3` doivent être disponibles sur la machine qui exécute l'analyse.
- Certaines fonctionnalités envisagées dans `conception.md` (keylogging, notifications administrateur en temps réel via WebSocket, gestion des formations suivies) ne sont pas implémentées dans le code actuel ; le document de conception doit être lu comme une proposition initiale, pas comme une description de l'état actuel du projet.

---

## Auteur

Projet développé [NOBRE Canisius](canisiusnobre@gmail.com)
