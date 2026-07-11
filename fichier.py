import os 
from google import genai
from dotenv import load_dotenv

# Charge les variables définies dans le fichier .env
load_dotenv()
client = genai.Client(api_key=os.getenv('APIKEY'))

# On liste simplement tout ce qui existe
for model in client.models.list():
    print(f"Modèle disponible : {model.name}")