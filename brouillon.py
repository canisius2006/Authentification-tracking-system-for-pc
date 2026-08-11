import requests 
def create_session(token):
    """Cette fonction va nous permettre de pouvoir créer une session quand l'utilisateur se connecte """
    url = "http://127.0.0.1:8000/api/session/"
    response = requests.post(url,headers={'Authorization':f"Bearer {token}"})
    id = response.json().get('id')
    print(id)

create_session("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg2NDUzNTkxLCJpYXQiOjE3ODY0NTE3OTEsImp0aSI6IjlmOGJiYzRmNTZkZjRjNzRiYWI0YzJiZDQyZWM3NjliIiwidXNlcl9pZCI6IjEifQ.fXBJP5vrPM8Xjf3pVArKmMfF0tz8gJA8AW7UE4xr1Gw")