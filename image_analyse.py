import ollama,time
t = time.time()
response = ollama.chat(
    model="llava",
    messages=[
        {
            "role": "user",
            "content": "Décris cette image en français.",
            "images": ["C:/Users/hp/Pictures/Screenshots/image.png"]
        }
    ]
)
print(time.time()-t,'s de traitement')
print(response["message"]["content"])
print(time.time()-t,'s après la reponse')