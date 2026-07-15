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
Mot de passe : CLUBIA
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

# Auteur
Canisius NOBRE
Projet développé pour le système d'inscription CAEB.
