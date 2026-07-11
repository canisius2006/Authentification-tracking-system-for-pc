from google import genai
from PIL import Image
import os,time 
from dotenv import load_dotenv 
load_dotenv()
a = time.time()
# 1. Configuration avec la nouvelle API
# Remplacez "VOTRE_CLE_API" par votre clé réelle
client = genai.Client(api_key=os.getenv('APIKEY'))

# 2. Chargement de l'image
image_path = "C:/Users/hp/Pictures/Screenshots/image.png"
img = Image.open(image_path)

# 3. Envoi de la requête
# Note : 'gemini-1.5-flash' est le nom correct et stable du modèle
try:
    response = client.models.generate_content(
        model="models/gemini-3.5-flash",
        contents=[
            "Analyse cette image et décris ce qu'elle contient. juste la description, je n'ai pas besoin de commentaire",
            img
        ]
    )

    print("\n--- Réponse de Gemini ---")
    print(response.text)

except Exception as e:
    print(f"Une erreur est survenue : {e}")

print(time.time()-a,'secondes')