import requests
import json

url = "http://localhost:11434/api/chat"

data = {
    "model": "qwen2.5:0.5b",
    "messages": [
        {"role": "user", "content": "Je code dans VS Code"}
    ]
}

response = requests.post(url, json=data, stream=True)

for line in response.iter_lines():
    if line:
        decoded = json.loads(line.decode("utf-8"))
        if "message" in decoded:
            print(decoded["message"].get("content", ""), end="")