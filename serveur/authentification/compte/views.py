from django.shortcuts import render
from django.http import HttpResponse,JsonResponse,HttpRequest
from django.contrib.auth import get_user_model 
from rest_framework import viewsets 
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from .serializers import UserSerializer,SessionActiviteSerializer,BadActionSerializer,ApplicationSerializer,RegisterSerializer,ActivationCompteSerializer,ProfilSerializer
#Import des classes du sérializers 
from .models import Session_activite,Application,Bad_action 
from rest_framework import generics 
from rest_framework.exceptions import ValidationError 
from rest_framework import serializers
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import APIView 
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status 
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle

from .tasks import verifier_activite
from dotenv import load_dotenv 
import os,socket
load_dotenv() 

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
     
class ProfilApiView(generics.RetrieveAPIView):
    serializer_class = ProfilSerializer 
    queryset = User.objects.all()
    def get_object(self):
        try:
            valeur = self.kwargs["valeur"]
        except :
            return self.request.user 
        
        utilisateur = User.objects.filter(
            Q(username=valeur) |
            Q(matricule=valeur) |
            Q(telephone=valeur) |
            Q(email=valeur)
        ).first()

        return utilisateur 
    

#En fait, on a juste besoin de créer une vue pour l'inscription 
#Parce que jwt gère déjà l'accès au token

class SessionActiviteModelView(viewsets.ModelViewSet):
    #On doit pouvoir uniquement voir sa session ici
    serializer_class = SessionActiviteSerializer
    def get_queryset(self):
        return Session_activite.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)
    
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
        application_id = self.request.data.get('application')
        try:
            application = Application.objects.get(id=int(application_id))
        except (ValueError, Application.DoesNotExist):
            application = Application.objects.filter(nom=application_id).first()
        if application is None:
            raise serializers.ValidationError(
            "Session invalide.")
        
        return serializer.save(application=application)
    
    permission_classes = [IsAuthenticated]


 

#Construction des api pour checker si les identifiants uniques n'existent pas déjà (username,email,telephone)
class CheckUsernameApiView(APIView):
    def get(self,request):
        user = request.query_params.get('user')
        if user is None:
            return Response(
                {'available':None,
                'username':user,
                'message':"Aucun user n'a été spécifié"}
            ,status=400)
        exist = User.objects.filter(Q(username__iexact = user)|Q(telephone__iexact=user)|Q(email__iexact=user)).exists()
        return Response(
            {
                'available':not exist,
                'username':user,
                'message': "Identifiant acceptable " if not exist else "identifiants Non disponibles "
            },status=200
        )

#Construction de la view api pour l'administrateur afin pour qu'il voir la liste des sessions par utilisateur

class VoirSessionUtilisateurApiView(APIView):
    #permission_classes = [IsAdminUser]
    def get(self,request):
        user = request.query_params.get('user')
        if user is None:
            return Response(
                {'available':None,
                'session':user,
                'message':"Aucun user n'a été spécifié"}
            ,status=400)
        utilisateur = User.objects.filter(Q(username__iexact = user)|Q(telephone__iexact=user)|Q(email__iexact=user)).first()

        liste_session = Session_activite.objects.filter(user=utilisateur)

        liste = list(liste_session.values())

        return Response(
            liste
        )



#Construction de la view api pour l'administrateur afin pour qu'il voir la liste des applications par session

class VoirApplicationSessionApiView(APIView):
    #permission_classes = [IsAdminUser]
    def get(self,request):
        session_id = request.query_params.get('session_id')
        if session_id is None:
            return Response(
                {'available':None,
                'username':session_id,
                'message':"Aucune session n'a été spécifié"}
            ,status=400)
        session = Session_activite.objects.filter(id=session_id).first()
        liste_application = Application.objects.filter(session = session)
        liste = list(liste_application.values())
        return Response(
            liste
        )


#Construction de la view api pour l'administrateur afin pour qu'il voir la liste des bad_actions par utilisateur

class VoirBadActionUtilisateurPerUserApiView(APIView):
    #permission_classes = [IsAdminUser]
    def get(self,request):
        user = request.query_params.get('user')
        if user is None:
            return Response(
                {'available':None,
                'session':user,
                'message':"Aucun user n'a été spécifié"}
            ,status=400)
        utilisateur = User.objects.filter(Q(username__iexact = user)|Q(telephone__iexact=user)|Q(email__iexact=user)).first()

        liste_bad_action = Bad_action.objects.filter(application__session__user = utilisateur)

        liste = list(liste_bad_action.values())

        return Response(
            liste
        )


#Construction de la view api pour l'administrateur afin pour qu'il voir la liste des bad_actions par session

class VoirBadActionUtilisateurPerSessionApiView(APIView):
    #permission_classes = [IsAdminUser]
    def get(self,request):
        session_id = request.query_params.get('session_id')
        if session_id is None:
            return Response(
                {'available':None,
                'session':session_id,
                'message':"Aucun session n'a été spécifié"}
            ,status=400)
        session = Session_activite.objects.filter(id=session_id).first()

        liste_bad_action = Bad_action.objects.filter(application__session=session)

        liste = list(liste_bad_action.values())

        return Response(
            liste
        )


class ListInscriptionPendingView(generics.ListAPIView):
    serializer_class = UserSerializer 
    queryset = User.objects.filter(is_active=False)
    
    permission_classes = [IsAdminUser]


class ValiderInscriptionApiView(APIView):
    throttle_scope = 'activation'
    @extend_schema(
        request=ActivationCompteSerializer,
        responses={
            200: OpenApiResponse(description="Compte activé avec succès"),
            404: OpenApiResponse(description="Utilisateur inexistant"),
            406: OpenApiResponse(description="Code d'activation incorrect"),
        },
        summary="Activer un compte utilisateur",
        description="Valide le code d'activation envoyé et active le compte si le code correspond.",
    )
    def post(self,request):
        serializer = ActivationCompteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:    
            user = User.objects.get(username = serializer.validated_data.get('username'))
        except User.DoesNotExist:
            return Response({'message':'Utilisateur inexistant'},status=status.HTTP_404_NOT_FOUND)
        activation_code = user.activation_code 
        if activation_code == serializer.validated_data.get('activation_code'):
            user.is_active = True 
            user.activation_code=None 
            user.save()

            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message':'compte activé',
                "refresh":str(refresh),
                "access":str(refresh.access_token)},
                status=status.HTTP_200_OK
            )
        
        else:
            return Response(
                {
                    'message':'Code incorrect'
                }
                ,
                    status=status.HTTP_406_NOT_ACCEPTABLE
            )


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

def dashboard(request):
    if request.user.is_superuser:
        return render(request,'dashboard.html')
    else:
        return HttpResponse("Vous n'êtes pas connecté en tant qu'administrateur ")






def ma_vue(request):
    return render(request,'test.html')


def profil(request,valeur):
    return render(request,'profil_2.html')

def termes(request):
    return render(request,'termes.html')

def guide(request):
    return render(request,'guide.html')

def extinction(request):
    """une vue pour montrer que l'ordinateur va s'éteindre """
    return render(request,'extinction.html')


def pending(request:HttpRequest):
    if request.user.is_superuser:
        return render(request,'pending.html')
    else:
        return  HttpResponse("Vous n'êtes pas connecté en tant qu'administrateur ") 

def session(request:HttpRequest):
    return render(request,'session.html')

def session_detail(request:HttpRequest):
    return render(request,'session_detail.html')