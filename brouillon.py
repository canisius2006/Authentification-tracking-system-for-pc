import requests,json
url = 'http://127.0.0.1:8000/api/check-user/'
data = requests.get(url,params={'user':'canisiusnobe@gmail.com'})
data = data.json()
a = data.get('available')
print(a)
