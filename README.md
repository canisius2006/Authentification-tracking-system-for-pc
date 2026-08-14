# Authentification-tracking-system-for-pc

Système d'authentification et de suivi automatique des utilisateurs sur les postes d'un cybercafé, avec attribution d'un score aux utilisateurs.

Le projet a évolué en deux versions :

- **V1** : le client communique directement avec MySQL.
- **V2** : le client conserve le principe et l'interface de la V1, mais passe par une **API REST Django/DRF** pour communiquer avec le serveur. La V2 ajoute également le suivi des activités et leur analyse asynchrone par IA.

La V1 n'est donc pas un projet différent : elle constitue la base du client dont la V2 reprend le fonctionnement général.

---

# Version 2.0 — Version actuelle

## 1. Architecture générale

Le projet est composé de deux parties principales :

- **`client/`** : application Python/CustomTkinter installée sur les postes clients.
- **`authentification/`** : serveur Django fournissant l'API REST, l'authentification JWT et le traitement des activités.

### Évolution de la communication entre les versions

```text
V1
Client CustomTkinter
        │
        │ MySQL Connector
        ▼
   Serveur MySQL


V2
Client CustomTkinter
        │
        │ HTTP / REST + JWT
        ▼
   API Django / DRF
        │
        ▼
     MySQL
```

Le fonctionnement côté client reste basé sur la configuration et les principes de la V1 : interface CustomTkinter, inscription de l'utilisateur, récupération du nom du poste, lancement automatique au démarrage et déploiement sous Windows.

La différence fondamentale est que **la V2 ne se connecte plus directement à MySQL depuis le client**. Les données sont envoyées à l'API Django, qui se charge de communiquer avec la base de données.

La V2 ajoute ensuite le suivi des activités :

```text
Client
  │
  │ activité de la fenêtre active
  │ toutes les 20 secondes
  ▼
API Django
  │
  ▼
Celery
  │
  ▼
Analyse IA
  │
  ├── activité correcte
  │
  └── mauvaise activité
          │
          ▼
     Bad_action
          │
          ▼
   Score utilisateur - 2
```

---

# 2. Fonctionnement du client

Le client est une application graphique développée avec **CustomTkinter**.

Il reprend les fonctionnalités principales de la V1 :

- interface d'inscription plein écran ;
- saisie du nom et du prénom ;
- validation des champs ;
- récupération automatique du nom du PC ;
- lancement automatique au démarrage de Windows ;
- génération d'un exécutable `.exe`.

La V2 ajoute :

- inscription en plusieurs étapes ;
- capture d'une photo de profil avec OpenCV ;
- connexion avec JWT ;
- rafraîchissement automatique du token ;
- suivi de la fenêtre/application active ;
- envoi périodique des activités à l'API ;
- récupération périodique du score ;
- avertissement lorsque le score atteint un seuil ;
- arrêt automatique du poste lorsque le score atteint 0.

La photo de profil est conservée en mémoire puis envoyée sous forme base64 ; elle n'est pas écrite sur le disque.

---

# 3. Suivi et analyse des activités

Le client détecte automatiquement l'application ou la fenêtre active et envoie les informations au serveur.

L'activité est envoyée toutes les **20 secondes**.

Le serveur reçoit notamment :

- le nom de l'application ;
- le titre de la fenêtre ;
- les informations nécessaires à l'identification de la session.

Lorsqu'une activité est enregistrée, Django déclenche une tâche Celery.

Le pipeline d'analyse est effectué en cascade :

1. détection de négation contextuelle ;
2. vérification d'une blocklist de domaines connus (`piracy.txt`) ;
3. détection de mots-clés de divertissement non ambigus ;
4. comparaison par embeddings avec des prototypes éducatifs et de divertissement ;
5. appel au LLM en dernier recours.

Si l'activité est considérée comme mauvaise :

- une `Bad_action` est créée ;
- **1 point est retiré au score de l'utilisateur**.

Le score initial est de **20 points**.

Le client vérifie ensuite régulièrement le score :

- à **10 points**, un avertissement est affiché ;
- à **0 point**, le poste est automatiquement éteint.

---

# 4. Serveur Django

Le répertoire `authentification/` contient le serveur.

Il fournit une API REST basée sur :

- Django ;
- Django REST Framework ;
- JWT ;
- MySQL.

Le serveur assure notamment :

- l'inscription ;
- la connexion ;
- la gestion des sessions ;
- la gestion des applications ;
- l'enregistrement des activités ;
- la gestion du score ;
- la création des `Bad_action`.

Le serveur sert également d'intermédiaire entre le client et MySQL.

Ainsi, le client n'a plus besoin de connaître les identifiants MySQL.

---

# 5. Traitement asynchrone

L'analyse des activités est réalisée avec :

- **Celery** : exécution des tâches en arrière-plan ;
- **Redis** : broker et backend de résultats ;
- **Ollama** : modèles d'IA.

Les modèles utilisés sont :

- `qwen2.5:1.5b` pour la classification générative ;
- `bge-m3` pour les embeddings.

---

# 6. Structure du projet

```text
.
├── authentification/                 # Serveur Django / API REST
│   ├── authentification/
│   │   ├── settings.py
│   │   ├── celery.py
│   │   └── urls.py
│   │
│   ├── compte/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── tasks.py
│   │   └── analyseur.py
│   │
│   ├── requirements.txt
│   └── manage.py
│
├── client/                          # Application installée sur les postes
│   ├── main_v2.py                   # Client actuel
│   ├── main_v1.py                   # Ancienne implémentation directe MySQL
│   ├── application_active.py        # Détection de la fenêtre active
│   ├── analyseur_version_api.py
│   └── tache_repetitif.py
│
├── piracy.txt                       # Blocklist
├── conception.md                    # Notes de conception
└── autres scripts d'expérimentation
```

`main_v1.py` peut être conservé dans le dépôt comme référence historique, mais il n'est plus nécessaire de documenter son fonctionnement séparément dans ce README : ses principes sont repris dans la V2.

---

# 7. Technologies utilisées

## Client

- Python 3.x
- CustomTkinter
- Tkinter
- Requests
- APScheduler
- OpenCV (`cv2`)
- Pillow
- PyWin32
- Psutil

## Serveur

- Python 3.x
- Django
- Django REST Framework
- `djangorestframework-simplejwt`
- `drf-spectacular`
- `drf-extra-fields`
- MySQL
- Celery
- Redis
- Ollama
- `python-dotenv`

## Déploiement

- Auto Py To Exe pour générer le `.exe`
- Windows
- Registre Windows / GPO pour le lancement automatique

---

# 8. Base de données

La base de données utilisée par le serveur est **MySQL**.

Dans la V1, le client accédait directement à cette base.

Dans la V2 :

```text
Client
   │
   │ HTTP
   ▼
Django REST API
   │
   │ ORM / connexion DB
   ▼
MySQL
```

Cette architecture permet de centraliser la logique d'accès aux données sur le serveur et d'éviter de distribuer les identifiants MySQL sur les postes clients.

La configuration de la base est effectuée côté serveur, notamment avec les variables d'environnement :

```env
SECRET_KEY=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_PORT=3306
```

L'hôte MySQL peut être configuré selon l'environnement de déploiement.

---

# 9. Installation

## 9.1 Prérequis

Installer :

- Python 3.x ;
- MySQL ;
- Redis ;
- Ollama.

Télécharger les modèles Ollama :

```bash
ollama pull qwen2.5:1.5b
ollama pull bge-m3
```

---

## 9.2 Installation du serveur

```bash
cd authentification
python -m venv venv
```

Sous Windows :

```bash
venv\Scripts\activate
```

Sous Linux/macOS :

```bash
source venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Si elles ne sont pas encore présentes dans `requirements.txt` :

```bash
pip install celery redis drf-extra-fields
```

Créer le fichier `.env` :

```env
SECRET_KEY=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_PORT=3306
```

Appliquer les migrations :

```bash
python manage.py migrate
```

Lancer Django :

```bash
python manage.py runserver
```

---

## 9.3 Lancer Redis

Dans un autre terminal :

```bash
redis-server
```

---

## 9.4 Lancer Celery

Depuis `authentification/` :

```bash
celery -A authentification worker --loglevel=info -P solo
```

L'option `-P solo` est recommandée sous Windows.

---

## 9.5 Documentation de l'API

Une fois Django lancé :

- Swagger : `/api/docs/`
- Redoc : `/api/redoc/`
- Schéma OpenAPI : `/api/schema/`

Avec le serveur local :

```text
http://127.0.0.1:8000/api/docs/
```

---

# 10. Installation du client

Depuis le dossier `client/` :

```bash
pip install customtkinter requests pillow opencv-python apscheduler pywin32 psutil
```

Lancer :

```bash
python main_v2.py
```

L'URL de l'API utilisée pour l'inscription et la connexion peut être configurée dans l'interface.

Pour un déploiement sur plusieurs postes, il est recommandé de centraliser cette URL dans une configuration plutôt que de la coder directement dans le programme.

---

# 11. Authentification

La V2 utilise une authentification **JWT**.

Le client obtient :

- un `access_token` ;
- un `refresh_token`.

L'`access_token` est utilisé pour authentifier les requêtes envoyées à l'API.

Le `refresh_token` permet d'obtenir un nouveau token lorsque l'ancien expire.

Le client effectue automatiquement le rafraîchissement périodique du token.

---

# 12. Génération du fichier EXE

Pour générer l'exécutable Windows :

```bash
pip install auto-py-to-exe
```

Puis :

```bash
auto-py-to-exe
```

Configurer :

- **Script Location** : `main_v2.py`
- **One File** : activé
- **Window Based** : activé
- ajouter l'icône si nécessaire.

Puis cliquer sur :

```text
Convert .py to .exe
```

Le fichier `.exe` peut ensuite être déployé sur les postes clients.

---

# 13. Lancement automatique de l'application

Pour lancer automatiquement l'application au démarrage de Windows, une entrée peut être ajoutée dans :

```text
HKEY_LOCAL_MACHINE
└── SOFTWARE
    └── Microsoft
        └── Windows
            └── CurrentVersion
                └── Run
```

Créer une valeur chaîne :

```text
AuthentificationCAEB
```

et lui attribuer le chemin de l'exécutable :

```text
"C:\Program Files\CAEB\AuthCAEB.exe"
```

La modification de `HKEY_LOCAL_MACHINE` nécessite des droits administrateur.

Pour un déploiement sur plusieurs machines, cette configuration peut être automatisée avec :

- un script d'installation ;
- une stratégie de groupe Windows (GPO) ;
- un outil de déploiement centralisé.

---

# 14. Raccourcis de fermeture

L'application bloque volontairement :

- `Alt + F4`
- `Ctrl + W`
- `Ctrl + Q`
- `Échap`

Une sortie administrateur est disponible avec :

```text
Ctrl + Shift + B
```

---

# 15. Différences entre V1 et V2

| Élément | V1 | V2 |
|---|---|---|
| Interface client | CustomTkinter | CustomTkinter |
| Inscription | Oui | Oui |
| Nom du PC | Oui | Oui |
| Lancement Windows | Oui | Oui |
| Génération `.exe` | Oui | Oui |
| Accès MySQL depuis le client | **Direct** | **Non** |
| API Django | Non | **Oui** |
| Authentification JWT | Non | **Oui** |
| Suivi des activités | Non | **Oui** |
| Celery | Non | **Oui** |
| Redis | Non | **Oui** |
| Analyse IA | Non | **Oui** |
| Score utilisateur | Non | **Oui** |
| `Bad_action` | Non | **Oui** |

La V2 doit donc être considérée comme **l'évolution de la V1**, et non comme une application entièrement différente.

La modification architecturale principale est le passage :

```text
V1 : Client → MySQL
```

à :

```text
V2 : Client → API Django → MySQL
```

La V2 ajoute ensuite toute la partie **tracking + score + analyse IA** autour de cette architecture.

---

# 16. Limitations connues

- `requirements.txt` du serveur doit être maintenu à jour avec toutes les dépendances réellement utilisées.
- L'URL de l'API ne devrait pas être codée en dur dans le client.
- `piracy.txt` doit être disponible à l'emplacement attendu par `analyseur.py`.
- Le déploiement multi-poste nécessite une configuration réseau correcte entre les clients et le serveur Django.
- Le serveur Django doit pouvoir accéder à MySQL.
- Celery doit pouvoir communiquer avec Redis.
- Ollama et les modèles nécessaires doivent être disponibles sur la machine qui effectue l'analyse.

---

# 17. Résumé

Le système a commencé avec une architecture simple :

```text
Poste client
    │
    └──► MySQL
```

La V2 conserve les bases du client et de son déploiement, mais introduit une architecture serveur :

```text
                    ┌──► MySQL
                    │
Poste client ──► API Django
                    │
                    └──► Celery ──► Redis
                              │
                              └──► Ollama / IA
```

Cette séparation permet de centraliser l'accès aux données, l'authentification, le suivi des activités et l'analyse des comportements côté serveur.

---

# Auteur

Projet développé pour le système d'inscription et de suivi CAEB.
