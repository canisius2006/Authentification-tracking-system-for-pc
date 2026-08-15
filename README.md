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
   Score utilisateur - 1
   (puis -1 supplémentaire tous les 6 signalements
    répétés de la même mauvaise action)
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
├── serveur/
│   ├── authentification/             # Projet Django / API REST
│   │   ├── authentification/
│   │   │   ├── settings.py
│   │   │   ├── celery.py
│   │   │   ├── wsgi.py / asgi.py
│   │   │   └── urls.py
│   │   │
│   │   ├── compte/
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── serializers.py
│   │   │   ├── authentication.py     # Backend d'authentification multi-champs
│   │   │   ├── tasks.py              # Tâche Celery verifier_activite
│   │   │   └── analyseur.py          # Pipeline d'analyse IA
│   │   │
│   │   ├── static/ , templates/
│   │   └── manage.py
│   │
│   └── piracy.txt                    # Blocklist utilisée par analyseur.py
│
├── client/                           # Application installée sur les postes
│   ├── main_v2.py                    # Client actuel
│   ├── main_v1.py                    # Ancienne implémentation directe MySQL
│   ├── application_active.py         # Détection de la fenêtre active (v1)
│   ├── application_monitor.py        # Détection des fenêtres visibles (v2)
│   └── application_topmost.py        # Détection de la fenêtre au premier plan
│
├── analyseur.py                      # Copie du pipeline d'analyse, pour tests hors serveur
├── compilateur_main.py               # Utilitaire graphique pour compiler le client avec Nuitka
├── lancer_serveur.py                 # Lance Redis/Memurai + Django (runserver) + Celery
├── lancer_serveur_worker.py          # Lance Waitress (production) + Celery
├── requirements.txt
├── conception.md                     # Notes de conception
└── icone.ico / drawSQL-image-export-*.webp
```

`main_v1.py` peut être conservé dans le dépôt comme référence historique, mais il n'est plus nécessaire de documenter son fonctionnement séparément dans ce README : ses principes sont repris dans la V2.

`analyseur.py` (racine) et `serveur/authentification/compte/analyseur.py` sont actuellement deux copies quasi identiques du même pipeline : à terme, un seul fichier partagé (importé par le serveur) éviterait qu'ils divergent.

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
DB_HOST=...
```

`DB_HOST` est résolu via `socket.gethostbyname()` dans `settings.py` : il doit donc être un nom d'hôte résolvable (ou une IP) au moment du démarrage du serveur, sans quoi Django ne démarre pas.

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

## 9.4bis Scripts de lancement automatisés (Windows)

Deux scripts à la racine du dépôt évitent d'ouvrir manuellement chaque terminal :

- **`lancer_serveur.py`** : détecte un `redis-cli`/`memurai-cli` fonctionnel, puis ouvre trois fenêtres PowerShell (Redis/Memurai, `manage.py runserver`, Celery worker). Adapté au développement.
- **`lancer_serveur_worker.py`** : ouvre deux fenêtres PowerShell (Waitress en écoute sur `0.0.0.0:8000`, Celery worker). Adapté à un déploiement plus proche de la production, sans le serveur de développement Django.

Les deux scripts lisent `DB_HOST` depuis `.env` pour construire l'adresse d'écoute, et supposent une arborescence `serveur/authentification/` avec un environnement virtuel `venv/` à la racine du projet.

⚠️ `lancer_serveur_worker.py` fait écouter Waitress sur `0.0.0.0`, donc sur toutes les interfaces réseau de la machine. Avec `DEBUG=True` et `ALLOWED_HOSTS=['*']` toujours actifs côté Django (voir §16.1), cela expose les pages d'erreur détaillées à tout le réseau accessible. Corriger §16.1 avant d'utiliser ce script en dehors d'un réseau de confiance.

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

# 16. Sécurité — points de vigilance identifiés

Cette section documente des points relevés lors d'une relecture du code, à corriger avant tout déploiement exposé au-delà d'un réseau local de confiance.

## 16.1 Configuration Django

- **`DEBUG = True`** est codé en dur dans `settings.py` (non piloté par une variable d'environnement). En production, cela expose les pages d'erreur Django détaillées (stack trace, requêtes SQL, valeurs de configuration) à quiconque déclenche une exception sur l'API.
- **`ALLOWED_HOSTS = ['*']`** accepte n'importe quel en-tête `Host`. Combiné à `DEBUG=True`, le risque de fuite d'informations est maximal.
- Recommandation : `DEBUG = os.getenv('DEBUG', 'False') == 'True'` et `ALLOWED_HOSTS` limité aux hôtes réellement utilisés, au moins pour tout déploiement hors poste de développement.

## 16.2 Endpoint de profil non protégé

`ProfilApiView` (`GET /api/profil/<valeur>/`) ne définit pas de `permission_classes` et hérite donc du comportement par défaut de DRF (accès non authentifié). `<valeur>` peut être un `username`, `matricule`, `email` ou `telephone`, et la réponse inclut l'email, le téléphone et le score de l'utilisateur. En l'état, n'importe qui connaissant (ou devinant) un identifiant peut consulter ces informations sans se connecter.
Recommandation : ajouter `permission_classes = [IsAuthenticated]`, et envisager de restreindre les champs renvoyés à l'utilisateur qui consulte son propre profil (sauf pour un admin).

## 16.3 Code d'activation de compte

Le code d'activation (`activation_code`) fait seulement 3 caractères (`create_code()` génère un nombre entre 112 et 999, soit moins de 900 valeurs possibles), et `ValiderInscriptionApiView` n'a ni authentification ni limitation de débit (*rate limiting*). Un script pourrait tester toutes les combinaisons en quelques minutes et activer un compte à la place de son propriétaire légitime.
Recommandation : allonger le code (6 chiffres ou plus), et/ou ajouter une limitation du nombre de tentatives par compte/IP (ex. `django-ratelimit`, ou le throttling intégré à DRF).

## 16.4 `ast.literal_eval` sur une donnée envoyée par le client

Dans `serializers.py`, `str_to_dict()` applique `ast.literal_eval()` au champ `nom` envoyé par le client dans `ApplicationSerializer`. `ast.literal_eval` n'exécute pas de code arbitraire (contrairement à `eval`), donc ce n'est pas une faille d'exécution de code, mais :
- toute valeur de `nom` qui n'est pas une syntaxe littérale Python valide fait planter la création (exception non gérée → erreur 500) ;
- le champ `nom` stocké en base finit par contenir la représentation texte d'un dictionnaire Python plutôt qu'un simple nom d'application, ce qui est fragile et peu lisible.
Recommandation : faire transiter cette donnée en JSON (`json.dumps` côté client, `json.loads` côté serveur) plutôt qu'en syntaxe littérale Python, et valider/encadrer les exceptions de parsing avec une réponse HTTP propre (400) plutôt que de laisser remonter une 500.

## 16.5 Trafic client ↔ serveur en HTTP simple

Le client (`main_v2.py`) construit toutes ses requêtes en `http://{HOST}/...` (voir `DEFAULT_API_BASE_URL`), sans TLS. Les identifiants de connexion et les tokens JWT transitent donc en clair sur le réseau. Sur un réseau local isolé et de confiance, le risque est limité ; sur un réseau partagé (Wi-Fi, VLAN mutualisé) ou si le serveur est un jour exposé sur Internet, c'est une interception facile (identifiants, tokens, activité de navigation des utilisateurs).
Recommandation : passer en HTTPS dès que le déploiement sort d'un réseau local strictement contrôlé (reverse proxy avec certificat, même auto-signé en interne).

## 16.6 Nom d'hôte du serveur codé en dur côté client

`HOST = f"{socket.gethostbyname('CIA-008')}:8000"` dans `main_v2.py` force la résolution DNS/NetBIOS du nom `CIA-008`. Cela fonctionne uniquement si ce nom d'hôte est résolvable depuis chaque poste client, et rend le client inutilisable tel quel sur un autre réseau ou avec un autre nom de serveur. C'est cohérent avec la limitation déjà notée plus bas (§17) sur l'URL codée en dur, mais mérite d'être isolé dans un fichier de configuration (ou récupéré au premier lancement via l'écran de connexion, qui propose déjà `api_base_url_var`).

---

# 17. Limitations connues

- `requirements.txt` du serveur doit être maintenu à jour avec toutes les dépendances réellement utilisées.
- L'URL de l'API ne devrait pas être codée en dur dans le client.
- `piracy.txt` doit être disponible à l'emplacement attendu par `analyseur.py`.
- Le déploiement multi-poste nécessite une configuration réseau correcte entre les clients et le serveur Django.
- Le serveur Django doit pouvoir accéder à MySQL.
- Celery doit pouvoir communiquer avec Redis.
- Ollama et les modèles nécessaires doivent être disponibles sur la machine qui effectue l'analyse.

---

# 18. Résumé

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
