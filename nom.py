import socket

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

print("Nom du PC :", hostname)
print("Adresse IP :", ip_address)

