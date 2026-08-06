from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import get_user_model 
from rest_framework import viewsets 
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from .serializers import UserSerializer,SessionActiviteSerializer,BadActionSerializer,ApplicationSerializer,RegisterSerializer,ActivationCompteSerializer
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
from .tasks import add

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


class ListInscriptionPendingView(generics.ListAPIView):
    serializer_class = UserSerializer 
    queryset = User.objects.filter(is_active=False)
    
    permission_classes = [IsAdminUser]


class ValiderInscriptionApiView(APIView):
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

def dash(request):
    return render(request,'pending.html')






def test_task(request):
    result = add.delay(2,3)
    return render(request,'task.html',{'result':result})


def test_task_result(request,task_id):
    result = add.AsyncResult(task_id)
    if result.ready():
        return render(request,'voir.html',{'results':result.result})
    return render(request,'voir.html',{'results':"Result not ready yet"})