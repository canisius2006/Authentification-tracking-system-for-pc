import mysql.connector 
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='CLUBIA',
    database='authentification'
)
cursor = conn.cursor()
# 1. Créer la table si elle n'existe pas
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    date VARCHAR(100),
    nom_pc VARCHAR(100)
)
""")