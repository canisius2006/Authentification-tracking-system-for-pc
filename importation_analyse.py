from client.analyseur import analyser_activite 
import json
activite = {'application': 'Code.exe', 'titre': 'test.py - developpement - Visual Studio Code'}
data = analyser_activite(activite)
print(json.dumps(data, indent=4, ensure_ascii=False))