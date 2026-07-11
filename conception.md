# Présentation du projet d'authentification des Ordinateurs Portables du CAEB

## 1. Présentation

Ce projet vise à mettre en place un système d'authentification, de suivi (tracking) et de gestion des utilisateurs des ordinateurs du laboratoire du CAEB. Il couple une base de données solide regroupant tous les membres du laboratoire à un mécanisme de suivi automatisé de l'utilisation des postes, afin de garantir une utilisation responsable et productive du matériel informatique mis à disposition.

## 2. Contexte

Ce projet a été créé pour permettre l'authentification et la connexion sur les ordinateurs du CAEB, autrement dit du laboratoire du CAEB. Couplé au tracking et à la conception d'une base de données solide pour tous les participants ou membres du laboratoire, il permettra un suivi plus détaillé de chaque membre.

## 3. Objectifs

- Garantir que chaque utilisation d'un ordinateur du laboratoire soit associée à un membre identifié.
- Fournir au responsable des PC une vue exhaustive et à jour des utilisateurs actifs.
- Encourager une utilisation productive et responsable des ordinateurs à travers un système de score moral.
- Automatiser le suivi des postes sans nécessiter une surveillance humaine permanente.
- Informer les administrateurs en temps réel en cas d'action jugée inappropriée.
- Construire une base de données centralisée et exploitable sur les membres, leurs formations suivies et leur usage du matériel.

## 4. Utilisateurs

- **Utilisateur / Membre du laboratoire** : s'inscrit, se connecte avec son numéro matricule et son mot de passe, utilise le PC normalement, et voit son score moral évoluer selon ses actions.
- **Responsable / Administrateur du CAEB** : consulte les profils, les scores, les historiques d'activité (keylog, applications, temps d'utilisation), et reçoit des notifications en cas d'action interdite.
- *(Proposition, à confirmer)* **Formateur / Encadrant** : rôle intermédiaire qui pourrait suivre uniquement les membres qu'il encadre, sans avoir tous les droits d'un administrateur.

## 5. Fonctionnalités

### 5.1 Inscription des utilisateurs
Chaque utilisateur ou membre du laboratoire du CAEB aura un profil propre, sauvegardé dans la base de données MySQL créée à cet effet. Il regroupera comme champs le **Nom**, les **Prénoms**, l'**âge**, l'**adresse email**, le **numéro téléphonique** *(facultatif)*, un **identifiant** ou **numéro matricule**, un **mot de passe**, et enfin une **photo de profil**. Tous ces champs seront renseignés lors de l'inscription de l'utilisateur à la plateforme.

En tant qu'entités liées à l'utilisateur, on retrouve également le **score moral** de l'individu, les **formations suivies**, le **keylog** de navigation (actions faites sur le PC), les **applications** ouvertes sur l'ordinateur, les **bad_actions** de l'utilisateur (susceptibles de lui retirer des points de moral), le **temps_pc** d'utilisation du PC et le **temps_application** d'utilisation des applications desktop et web.

### 5.2 Connexion de l'utilisateur
À partir de son **numéro matricule** et de son **mot de passe**, l'utilisateur pourra se connecter à la plateforme. Il bénéficiera d'un score initial de 20/20 comme score moral, qui se réduira suivant ce qu'il fera sur son PC, sur le modèle du système de points du permis de conduire.

### 5.3 Tracking à partir du nom des applications actives et du keylogging
Cette fonctionnalité a pour but de lancer un thread sur le PC après authentification, afin de suivre l'utilisateur à partir de ses actions, et de lui retirer des points selon la gravité de ces actions ou de ces recherches, si elles ne sont pas en rapport avec la programmation.

### 5.4 Système de score moral
Ce score, dont la limite est fixée à **20**, permet de juger le comportement de l'utilisateur suivi. Fonctionnant sur le modèle des points du permis de conduire, il diminue automatiquement en fonction des actes commis, analysés par une IA locale.

### 5.5 Notifications en temps réel
Les membres administrateurs seront informés en temps réel lorsqu'une action interdite est commise par un utilisateur.

### 5.6 *(Proposition)* Tableau de bord administrateur
Une interface web (accessible via Django) permettant au responsable de visualiser en un coup d'œil : la liste des membres connectés, leur score moral, l'historique de leurs actions récentes et les alertes en cours.

## 6. Contraintes

- **Contrainte technique** : latence dans l'envoi et le traitement des requêtes vers l'API du LLM local, utilisé pour l'analyse des titres de fenêtres et des actions effectuées.
- **Contrainte technique** : pas de compréhension d'image combinée au tracking pour le moment (voir section Limites).
- **Contrainte matérielle** : le LLM local doit pouvoir fonctionner sur les machines disponibles au CAEB, ce qui limite la taille du modèle utilisable.
- **Contrainte éthique et légale** *(proposition, à valider avec le responsable du CAEB)* : informer clairement chaque utilisateur, lors de son inscription, que ses actions sur le PC (applications ouvertes, frappes clavier, temps d'utilisation) seront suivies et analysées, et recueillir son consentement explicite. Il est recommandé d'exclure du keylog les champs de saisie de mots de passe (y compris ceux d'autres services) pour éviter tout risque de fuite de données sensibles.
- **Contrainte de sécurité** : les mots de passe des utilisateurs doivent être stockés sous forme hachée (le système d'authentification de Django gère cela nativement).

## 7. Limites de la plateforme

- Pour le moment, il n'est pas possible de combiner la compréhension d'images au tracking ; cette fonctionnalité pourra être ajoutée via des logiciels de surveillance de masse de PC.
- Nous pouvons avoir de la latence dans l'envoi et le traitement des requêtes à l'API de notre LLM local, utilisé pour aider à la compréhension des titres et des actions en train d'être effectuées par l'utilisateur.

## 8. Technologies

Le langage **Python** sera le plus utilisé côté backend, ainsi que pour le développement des applications desktop sur les PC utilisateurs. Étant donné le besoin de construire un serveur pour les utilisateurs, **Django** sera utilisé pour l'authentification ainsi que la gestion des utilisateurs. À cela s'ajoute le framework **Django REST Framework** pour les API vers le serveur, afin de faciliter la liaison entre les applications et le serveur.

Pour la conception des applications desktop, nous utiliserons **CustomTkinter** et le module **requests** pour les appels API.

Il sera également possible d'envoyer des notifications en temps réel aux membres administrateurs pour les informer lorsqu'une action interdite est commise *(proposition : via Django Channels + WebSocket pour le temps réel)*.

Base de données : **MySQL**.

*(Proposition, à confirmer)* LLM local : un modèle léger exécuté via **Ollama** (ou équivalent) pourrait être utilisé pour l'analyse des titres de fenêtres et des actions, afin de limiter la latence évoquée dans les limites du projet.

## 9. Architecture

Le projet est mené dans un cadre agile : l'architecture se précisera au fur et à mesure de l'avancement. L'important, à ce stade, est de connaître les grandes fonctions en jeu.

**Proposition de schéma général** :

1. **Application desktop (CustomTkinter)** installée sur chaque PC du laboratoire : gère l'authentification locale, lance le thread de tracking après connexion, et communique avec le serveur via l'API REST (module `requests`).
2. **Serveur Django + DRF** : expose les endpoints d'authentification, de gestion des profils, de réception des logs de tracking, et de calcul/mise à jour du score moral.
3. **Module d'analyse IA locale** : reçoit les titres de fenêtres et actions, les évalue, et renvoie une note ou une pénalité à appliquer au score moral.
4. **Base de données MySQL** : stocke les profils, scores, formations, logs, et bad_actions.
5. **Canal de notification temps réel** *(proposition : Django Channels)* : pousse une alerte vers le tableau de bord administrateur dès qu'une action interdite est détectée.

## 10. Planning

### Étape 1 — Création du serveur Django
Django sera particulièrement intéressant ici, car nous voulons faire de l'authentification de compte. De plus, nous voulons créer des tables de données ayant des relations entre elles ; nous commencerons donc par la création du serveur Django.

### Étape 2 — Création des tables relationnelles avec leurs champs précis
Nous penchons vers la création des tables suivantes :

**Profil**

| Profil |
|:-------:|
| Matricule (primary key) |
| Noms |
| Prénoms |
| Photo de profil |
| Adresse électronique |
| Numéro téléphonique |
| Mot de passe |

**Score**

| Score |
|:----:|
| Matricule (foreign key) |
| Valeur |

*(Proposition — tables complémentaires à définir)*

**Bad_action**

| Bad_action |
|:----:|
| Matricule (foreign key) |
| Description |
| Gravité |
| Date |
| Points_retirés |

**Session_activite**

| Session_activite |
|:----:|
| Matricule (foreign key) |
| Application |
| Temps_pc |
| Temps_application |
| Date_debut |
| Date_fin |

**Formation**

| Formation |
|:----:|
| Matricule (foreign key) |
| Intitulé |
| Date |

### Étape 3 — Développement de l'API d'authentification (Django REST Framework)
Mise en place des endpoints d'inscription, de connexion et de gestion du profil.

### Étape 4 — Développement de l'application desktop (CustomTkinter)
Interface de connexion locale et intégration des appels API via `requests`.

### Étape 5 — Intégration du thread de tracking (applications actives + keylogging)
Mise en place de la remontée périodique des logs vers le serveur.

### Étape 6 — Intégration du module d'analyse IA locale et du système de score moral
Connexion du LLM local à l'API, calcul automatique des pénalités.

### Étape 7 — Mise en place des notifications temps réel pour les administrateurs

### Étape 8 — Développement du tableau de bord administrateur

### Étape 9 — Tests, corrections et déploiement sur les postes du CAEB

*(Les dates précises de chaque étape restent à définir selon votre calendrier.)*

## 11. Budget

*(À compléter selon vos besoins réels — proposition de postes à considérer si le projet dépasse le cadre strictement académique)* :
- Hébergement du serveur (VPS) si déploiement au-delà du réseau local du laboratoire.
- Nom de domaine, le cas échéant.
- Éventuels coûts liés à l'exécution du LLM local (matériel, énergie) si un serveur dédié est nécessaire.
- Pour un usage strictement interne au laboratoire (serveur hébergé sur place, PC déjà existants), le budget peut être considéré comme nul ou minime.

## 12. Annexes

### A. Environnement de développement
```
pip install pathlib
```
*(À compléter avec l'ensemble des dépendances du projet : django, djangorestframework, mysqlclient, customtkinter, requests, etc.)*

### B. Modèle Conceptuel de Données (MCD)
Schéma des relations entre les entités principales du projet, en notation Mermaid (`erDiagram`). Ce bloc peut être collé tel quel dans n'importe quel outil supportant Mermaid (voir explication plus bas).

```
erDiagram
  PROFIL ||--|| SCORE : possede
  PROFIL ||--o{ BAD_ACTION : commet
  PROFIL ||--o{ SESSION_ACTIVITE : genere
  PROFIL ||--o{ FORMATION : suit
  PROFIL {
    string matricule PK
    string noms
    string prenoms
    string email
    string mot_de_passe
  }
  SCORE {
    string matricule FK
    int valeur
  }
  BAD_ACTION {
    string matricule FK
    string description
    string gravite
    date date
    int points_retires
  }
  SESSION_ACTIVITE {
    string matricule FK
    string application
    int temps_pc
    date date_debut
  }
  FORMATION {
    string matricule FK
    string intitule
    date date
  }
```

**Lecture des cardinalités** :
- `||--||` : un et un seul de chaque côté (relation 1,1) — ex. un Profil a exactement un Score.
- `||--o{` : un profil peut être lié à zéro, une ou plusieurs occurrences (relation 0,n) — ex. un Profil peut avoir zéro ou plusieurs Bad_action.

### C. Glossaire
- **Score moral** : indicateur de comportement de l'utilisateur, initialisé à 20/20, diminuant selon la gravité des actions jugées inappropriées.
- **Bad_action** : action de l'utilisateur jugée non conforme à l'usage prévu des PC (hors programmation).
- **Keylog** : enregistrement des actions/frappes effectuées par l'utilisateur sur le poste.