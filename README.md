# Authentification-tracking-system-for-pc
Pour l'authentification des utilisateurs sur les Ordinateurs d'un cyber, la suivi automatique sans suivi boosté à l'ia avec attribution de scores aux utilisateurs(système de points d'un permis de conduire)


## Version 1.0 
# Authentification CAEB - Système d'inscription

## Description

**Authentification CAEB** est une application graphique développée en Python avec **CustomTkinter** permettant d'enregistrer les utilisateurs lors de leur première utilisation sur un poste informatique.

L'application :

* affiche une interface d'inscription plein écran ;
* demande le nom et le prénom de l'utilisateur ;
* effectue une validation des champs saisis ;
* récupère automatiquement le nom du poste informatique ;
* enregistre les informations dans une base de données MySQL distante ;
* peut être configurée pour se lancer automatiquement au démarrage de Windows.

---

## Fonctionnalités

* Interface graphique moderne avec `customtkinter`.
* Validation automatique du nom et du prénom.
* Détection automatique du nom du PC.
* Connexion à une base MySQL.
* Enregistrement :

  * Nom de l'utilisateur ;
  * Prénom ;
  * Date et heure d'inscription ;
  * Nom du poste informatique.
* Exécution automatique au démarrage du système.

---

## Technologies utilisées

* Python 3.x
* CustomTkinter
* Tkinter
* MySQL Connector
* MySQL Server
* Auto Py To Exe (conversion en fichier `.exe`)

---

## Installation des dépendances

Avant d'exécuter le script, installer les bibliothèques nécessaires :

```bash
pip install customtkinter mysql-connector-python
```

---

## Configuration de la base de données MySQL

L'application nécessite une base de données MySQL appelée :

```
authentification
```

La table utilisée est :

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    date DATETIME,
    nom_pc VARCHAR(100)
);
```

Le compte MySQL utilisé par l'application doit avoir les droits d'insertion :

```
Utilisateur : inscription
Mot de passe : ******
Base : authentification
```

Le serveur MySQL doit être accessible depuis les postes clients.

---

## Configuration réseau

Dans le script, l'adresse IP du serveur MySQL est récupérée grâce au nom réseau :

```python
adresse_ip = socket.gethostbyname('CIA-008')
```

Le poste serveur doit donc être accessible avec le nom :

```
CIA-008
```

ou cette ligne doit être modifiée avec l'adresse IP fixe du serveur.

Exemple :

```python
adresse_ip = "192.168.1.10"
```

---

# Génération du fichier EXE

Pour générer un exécutable Windows :

1. Installer Auto Py To Exe :

```bash
pip install auto-py-to-exe
```

2. Lancer :

```bash
auto-py-to-exe
```

3. Choisir :

   * **Script Location** : le fichier Python principal.
   * **One File** : activé.
   * **Window Based** : activé (pas de console).
   * Ajouter les icônes si nécessaire.

4. Cliquer sur :

```
Convert .py to .exe
```

Le fichier `.exe` généré pourra être déployé sur les postes utilisateurs.

---

# Exécution automatique au démarrage Windows

Pour permettre au programme de se lancer automatiquement au démarrage du PC, il faut ajouter une entrée dans le registre Windows.

## Modification du registre HKLM

Ouvrir :

```
regedit
```

Puis aller dans :

```
HKEY_LOCAL_MACHINE
 └── SOFTWARE
     └── Microsoft
         └── Windows
             └── CurrentVersion
                 └── Run
```

Dans la clé :

```
Run
```

Créer une nouvelle valeur :

```
Clic droit → Nouveau → Valeur chaîne
```

Nom de la valeur :

```
AuthentificationCAEB
```

Données de la valeur :

```
"C:\Chemin\Vers\AuthCAEB.exe"
```

Exemple :

```
"C:\Program Files\CAEB\AuthCAEB.exe"
```

---

## Résultat

À chaque démarrage de Windows :

1. Le système consulte la clé :

```
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
```

2. Il détecte :

```
AuthentificationCAEB
```

3. Il exécute automatiquement :

```
AuthCAEB.exe
```

L'application apparaît alors directement sur l'écran d'inscription.

---

# Droits administrateur

La modification de :

```
HKEY_LOCAL_MACHINE
```

nécessite des droits administrateur.

Lors du déploiement sur plusieurs machines, il est recommandé d'effectuer cette étape :

* via un script d'installation ;
* via une stratégie de groupe Windows (GPO) ;
* ou avec un outil de déploiement centralisé.

---

# Raccourcis de fermeture

L'application bloque volontairement plusieurs raccourcis Windows :

* `Alt + F4`
* `Ctrl + W`
* `Ctrl + Q`
* `Échap`

Une sortie administrateur est disponible avec :

```
Ctrl + Shift + B
```

---

# Structure du projet

Exemple :

```
CAEB/
│
├── main.py
├── AuthCAEB.exe
├── README.md
│
└── ressources/
    └── icone.ico
```

---

# Déploiement conseillé

Pour un environnement professionnel :

1. Installer MySQL sur un serveur accessible.
2. Créer la base `authentification`.
3. Générer le fichier `.exe`.
4. Copier l'exécutable sur les postes clients.
5. Ajouter la clé registre HKLM automatiquement.
6. Redémarrer les postes pour vérifier l'exécution automatique.

---


#Version 2.0

# Authentification-tracking-system-for-pc

Pour l'authentification des utilisateurs sur les ordinateurs d'un cyber, avec suivi automatique boosté à l'IA et attribution de scores aux utilisateurs (système de points façon permis de conduire).

Le projet est composé de deux parties :

- **`authentification/`** — le serveur : une API REST Django (DRF + JWT), avec un pipeline d'analyse IA asynchrone (Celery + Redis + Ollama) qui juge chaque activité utilisateur.
- **`client/`** — l'application de poste : une app CustomTkinter qui gère l'inscription, la connexion, et le suivi (fenêtre active, score) en tâche de fond.

> ℹ️ Le dépôt contient deux versions du client : `main_v2.py` est la version actuelle, connectée à l'API. `main_v1.py` est l'ancienne version (v1.0), qui écrivait directement dans MySQL sans API, IA, Celery ni Redis ; elle est conservée à titre historique (voir tout en bas de ce document) mais n'est plus celle utilisée en production.

---

## Architecture

```
Client (main_v2.py, CustomTkinter)
   │  requêtes REST + JWT (login/inscription), toutes les 20s poste l'app active
   ▼
Serveur Django REST (authentification/)
   │  à l'enregistrement d'une activité (ApplicationSerializer.create)
   ▼
Celery (tâche verifier_activite) ──► Redis (broker + result backend)
   │
   ▼
Pipeline d'analyse (compte/analyseur.py), en cascade :
   1. Détection de négation contextuelle (ex. "comment arrêter de regarder des séries")
   2. Blocklist de domaines connus (piracy.txt)
   3. Mots-clés de contenu de divertissement non ambigus (trailer, episode N, vostfr, gameplay...)
   4. Similarité d'embeddings (modèle Ollama bge-m3) contre des prototypes éducatif / divertissement
   5. LLM génératif (modèle Ollama qwen2.5:1.5b), en dernier recours, avec double appel et rejet en cas de désaccord
   │
   ▼
Si "mauvais" : création d'un Bad_action + retrait de 2 points au score de l'utilisateur
```

Le client interroge son score toutes les minutes ; en dessous d'un certain seuil il avertit l'utilisateur, et à 0 il éteint automatiquement le poste.

---

## Structure du projet

```
.
├── authentification/            # Serveur Django (API REST)
│   ├── authentification/        # Settings, config Celery, urls racine
│   │   ├── settings.py
│   │   ├── celery.py
│   │   └── urls.py
│   ├── compte/                  # App principale
│   │   ├── models.py            # User, Session_activite, Application, Bad_action
│   │   ├── views.py / urls.py   # Endpoints DRF
│   │   ├── serializers.py       # Déclenche la tâche Celery à la création d'une Application
│   │   ├── tasks.py             # Tâche Celery verifier_activite
│   │   └── analyseur.py         # Pipeline de classification IA
│   ├── requirements.txt
│   └── manage.py
├── client/                      # Application de poste (CustomTkinter)
│   ├── main_v2.py                # Version actuelle : login/inscription API + tracking + score
│   ├── main_v1.py                 # Ancienne version (v1.0), dépréciée — voir en bas
│   ├── application_active.py     # Détection de la fenêtre active (win32gui/psutil)
│   ├── analyseur_version_api.py  # Variante du pipeline d'analyse appelant Ollama en HTTP direct
│   └── tache_repetitif.py
├── piracy.txt                    # Blocklist de domaines streaming/piraterie utilisée par analyseur.py
├── conception.md                 # Notes de conception
└── analyseur.py, keyloger.py, ollama_webuse.py, ...  # scripts d'expérimentation à la racine
```

---

## Fonctionnalités (v2)

- Inscription en plusieurs étapes, avec capture de photo de profil directement via la webcam (OpenCV), intégrée dans la même fenêtre. La photo n'est jamais écrite sur disque : elle est gardée en mémoire puis encodée en base64 à l'envoi.
- Connexion par JWT (access/refresh), avec rafraîchissement automatique du token toutes les 25 minutes.
- Suivi automatique de l'application/fenêtre active, posté au serveur toutes les 20 secondes.
- Score de moralité : chaque utilisateur démarre à 20 points ; chaque activité jugée "mauvaise" par le pipeline IA en retire 2. Le client vérifie le score chaque minute, avertit l'utilisateur à 10, et éteint automatiquement le poste si le score atteint 0.
- Documentation d'API générée automatiquement (drf-spectacular) : Swagger sur `/api/docs/`, Redoc sur `/api/redoc/`, schéma OpenAPI sur `/api/schema/`.

---

## Technologies utilisées

### Serveur (`authentification/`)
- Python 3.x, Django, Django REST Framework
- `djangorestframework-simplejwt` (authentification par JWT)
- `drf-spectacular` (documentation API auto-générée)
- `drf-extra-fields` (upload de photo de profil en base64)
- MySQL (`mysqlclient` / `mysql-connector-python`)
- **Celery** + **Redis** (broker et result backend) pour le traitement asynchrone des activités
- **Ollama**, avec les modèles `qwen2.5:1.5b` (classification générative) et `bge-m3` (embeddings)
- `python-dotenv` (variables d'environnement)

### Client (`client/`)
- Python 3.x, CustomTkinter, Tkinter
- `requests` (appels à l'API REST)
- `APScheduler` (rafraîchissement de token, envoi périodique de l'activité, vérification du score)
- OpenCV (`cv2`) pour la capture webcam intégrée
- Pillow (traitement d'image)
- `pywin32` / `psutil` (détection de la fenêtre active, spécifique Windows)

> ⚠️ **À propos de `authentification/requirements.txt`** : ce fichier date encore de la v1 et ne liste pas certaines dépendances utilisées par le code actuel du serveur, notamment `celery`, `redis` et `drf-extra-fields`. En attendant sa mise à jour, installez-les manuellement (voir ci-dessous). Le fichier mélange par ailleurs des dépendances client (customtkinter, pywin32...) et serveur, à séparer idéalement en deux fichiers distincts.

---

## Installation

### 1. Prérequis

- Python 3.x
- Un serveur MySQL accessible
- Un serveur **Redis** (broker Celery)
- **Ollama** installé, avec les modèles téléchargés :

```bash
ollama pull qwen2.5:1.5b
ollama pull bge-m3
```

### 2. Serveur (`authentification/`)

```bash
cd authentification
python -m venv venv
venv\Scripts\activate        # ou : source venv/bin/activate
pip install -r requirements.txt
pip install celery redis drf-extra-fields   # dépendances manquantes du requirements.txt actuel
```

Créer un fichier `.env` à la racine de `authentification/` avec au minimum :

```
SECRET_KEY=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_PORT=3306
```

L'hôte MySQL est actuellement résolu via le nom réseau `CIA-008` (voir `settings.py`) ; à adapter si votre serveur MySQL a un autre nom ou une IP fixe.

Copier `piracy.txt` (situé à la racine du dépôt) dans le répertoire d'où le serveur est lancé (`authentification/`), car `compte/analyseur.py` le charge par un chemin relatif.

Appliquer les migrations et lancer le serveur :

```bash
python manage.py migrate
python manage.py runserver
```

Dans un second terminal, lancer Redis s'il n'est pas déjà en service :

```bash
redis-server
```

Dans un troisième terminal, lancer un worker Celery (depuis `authentification/`) :

```bash
celery -A authentification worker --loglevel=info -P solo
```

(l'option `-P solo` est recommandée sous Windows ; sous Linux/Mac, le pool par défaut convient.)

La documentation interactive de l'API est ensuite disponible sur `http://127.0.0.1:8000/api/docs/`.

### 3. Client (`client/`)

```bash
cd client
pip install customtkinter requests pillow opencv-python apscheduler pywin32 psutil
python main_v2.py
```

L'URL de l'API pour la connexion/inscription est configurable dans l'interface (valeur par défaut : `http://127.0.0.1:8000/api/`). En revanche, l'URL utilisée par le suivi en tâche de fond (envoi de l'activité, vérification du score, rafraîchissement du token — classe `Coeur`) est actuellement codée en dur sur `http://127.0.0.1:8000` dans `main_v2.py` ; à externaliser en configuration pour un déploiement multi-poste.

---

## Notes / limitations connues

- `requirements.txt` du serveur n'est pas encore aligné avec le code (voir avertissement ci-dessus).
- L'URL de l'API utilisée par le tracking en arrière-plan est codée en dur dans `main_v2.py`.
- `piracy.txt` doit être copié dans le dossier d'exécution du serveur (chemin relatif dans `analyseur.py`).
- `main_v1.py` et sa documentation ci-dessous sont conservés pour mémoire mais ne reflètent plus le fonctionnement actuel du système.

---

## Version 1.0 (historique — dépréciée)

Cette section documente `main_v1.py`, l'ancienne version du client, qui n'est plus utilisée en production : elle écrit directement dans une base MySQL locale, sans passer par l'API, Celery, Redis ni l'IA.

# Authentification CAEB - Système d'inscription (v1)

## Description

**Authentification CAEB v1** est une application graphique développée en Python avec **CustomTkinter** permettant d'enregistrer les utilisateurs lors de leur première utilisation sur un poste informatique.

L'application :

- affiche une interface d'inscription plein écran ;
- demande le nom et le prénom de l'utilisateur ;
- effectue une validation des champs saisis ;
- récupère automatiquement le nom du poste informatique ;
- enregistre les informations dans une base de données MySQL distante ;
- peut être configurée pour se lancer automatiquement au démarrage de Windows.

### Technologies utilisées (v1)

- Python 3.x
- CustomTkinter
- Tkinter
- MySQL Connector
- MySQL Server
- Auto Py To Exe (conversion en fichier `.exe`)

### Installation des dépendances (v1)

```bash
pip install customtkinter mysql-connector-python
```

### Configuration de la base de données MySQL (v1)

L'application nécessite une base de données MySQL appelée `authentification`, avec la table :

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    date DATETIME,
    nom_pc VARCHAR(100)
);
```

Le compte MySQL utilisé par l'application doit avoir les droits d'insertion :

```
Utilisateur : inscription
Mot de passe : ******
Base : authentification
```

Le serveur MySQL doit être accessible depuis les postes clients.

### Configuration réseau (v1)

Dans le script, l'adresse IP du serveur MySQL est récupérée grâce au nom réseau :

```python
adresse_ip = socket.gethostbyname('CIA-008')
```

Le poste serveur doit donc être accessible avec le nom `CIA-008`, ou cette ligne doit être modifiée avec l'adresse IP fixe du serveur, par exemple :

```python
adresse_ip = "192.168.1.10"
```

### Génération du fichier EXE (v1)

Pour générer un exécutable Windows :

1. Installer Auto Py To Exe : `pip install auto-py-to-exe`
2. Lancer : `auto-py-to-exe`
3. Choisir :
   - **Script Location** : le fichier Python principal.
   - **One File** : activé.
   - **Window Based** : activé (pas de console).
   - Ajouter les icônes si nécessaire.
4. Cliquer sur **Convert .py to .exe**.

Le fichier `.exe` généré pourra être déployé sur les postes utilisateurs.

### Exécution automatique au démarrage Windows (v1)

Pour permettre au programme de se lancer automatiquement au démarrage du PC, il faut ajouter une entrée dans le registre Windows.

Ouvrir `regedit`, puis aller dans :

```
HKEY_LOCAL_MACHINE
 └── SOFTWARE
     └── Microsoft
         └── Windows
             └── CurrentVersion
                 └── Run
```

Créer une nouvelle valeur chaîne nommée `AuthentificationCAEB`, avec pour données le chemin de l'exécutable, par exemple :

```
"C:\Program Files\CAEB\AuthCAEB.exe"
```

À chaque démarrage de Windows, le système consulte cette clé, détecte `AuthentificationCAEB` et exécute automatiquement `AuthCAEB.exe`. L'application apparaît alors directement sur l'écran d'inscription.

La modification de `HKEY_LOCAL_MACHINE` nécessite des droits administrateur. Lors du déploiement sur plusieurs machines, il est recommandé d'effectuer cette étape via un script d'installation, une stratégie de groupe Windows (GPO), ou un outil de déploiement centralisé.

### Raccourcis de fermeture (v1)

L'application bloque volontairement plusieurs raccourcis Windows : `Alt + F4`, `Ctrl + W`, `Ctrl + Q`, `Échap`. Une sortie administrateur est disponible avec `Ctrl + Shift + B`.


---




# Auteur

Projet développé pour le système d'inscription CAEB.
