from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import get_user_model 
from rest_framework import viewsets 
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer

# Create your views here.



def accueil(request):
    return HttpResponse("Bienvenue sur l'api d'authentification")


User = get_user_model()

#Cette classe est pour l'inscription des utilisateurs
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    