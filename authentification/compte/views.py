from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import get_user_model 
from rest_framework import viewsets 
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from .serializers import UserSerializer,SessionActiviteSerializer,BadActionSerializer,ApplicationSerializer,RegisterSerializer
#Import des classes du sérializers 
from .models import Session_activite,Application,Bad_action 
from rest_framework import generics 
from rest_framework.exceptions import ValidationError 
from rest_framework import serializers
# Create your views here.



def accueil(request):
    return HttpResponse("Bienvenue sur l'api d'authentification")


User = get_user_model()

#Cette classe est pour l'administrateur, pour vérifier les utilisateurs 
class UserModelView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class RegisterApiView(generics.CreateAPIView):
    """Inscription d'un nouvel utilisateur """
    serializer_class = RegisterSerializer
     


#En fait, on a juste besoin de créer une vue pour l'inscription 
#Parce que jwt gère déjà l'accès au token

class SessionActiviteModelView(viewsets.ModelViewSet):
    #On doit pouvoir uniquement voir sa session ici
    serializer_class = SessionActiviteSerializer
    def get_queryset(self):
        return Session_activite.objects.filter(user=self.request.user)
    
    
    permission_classes = [IsAuthenticated]

class ApplicationModelView(viewsets.ModelViewSet):
    
    serializer_class = ApplicationSerializer 
    def get_queryset(self):
        return Application.objects.filter(session__user=self.request.user)
    
    def perform_create(self, serializer):
        session_id = self.request.data.get('session')
        session = Session_activite.objects.filter(user=self.request.user,id=session_id).first()
        if session is None:
            raise serializers.ValidationError(
            "Session invalide."
        )
        return serializer.save(session=session)
    
    permission_classes = [IsAuthenticated]

class Bad_actionModelView(viewsets.ModelViewSet):
    
    serializer_class = BadActionSerializer
    def get_queryset(self):
        return Bad_action.objects.filter(application__session__user=self.request.user)
    
    def perform_create(self, serializer):
        session_id = self.request.data.get('session')
        session = Session_activite.objects.filter(user=self.request.user,id=session_id).first()
        if session is None:
            raise serializers.ValidationError(
            "Session invalide.")
        application = Application.objects.filter(session=session,nom=self.request.data['nom']).first()
        if application is None:
            raise ValidationError( "L'application n'existe pas encore")
        return serializer.save(application=application)
    
    permission_classes = [IsAuthenticated]


