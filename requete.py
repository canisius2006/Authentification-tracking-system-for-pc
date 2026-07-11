import os
from google import genai
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv('APIKEY'))

response = client.models.generate_content(
    model='models/gemini-3.5-flash',
    contents='Pourquoi le ciel est-il bleu ? ne dépasses pas 5 mots',
)

print(response.text)

