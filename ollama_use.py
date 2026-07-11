from ollama import chat

response = chat(
    model='qwen2.5:0.5b',
    messages=[{'role': 'user', 'content': 'Hello!'}],
)
print(response.message.content)