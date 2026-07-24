from rest_framework import serializers 
from .models import Session_activite,Application,Bad_action
from django.contrib.auth import get_user_model 
User = get_user_model()

#Ce serializer sert à consulter ou modifier le profil.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email','matricule','password','photo_de_profil','telephone','sexe','score','created_at','updated_at']
        read_only_fields = ['id','created_at','updated_at']


#Celui-ci est utilisé uniquement lors de l'inscription.
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,min_length=8)

    class Meta:
        model = User 
        fields = ["username",'password','email','telephone','photo_de_profil','sexe']

        def create(self,validated_data):
            return User.objects.create_user(**validated_data)


#cette classe pour l'enregistrement de la session utilisateur 
class SessionActiviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session_activite
        fields = ["id","jour","heure_debut","heure_fin"]

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Application
        fields = ['id','session','nom','heure_debut','heure_fin']
        read_only_fields = ['heure_debut']

class BadActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bad_action
        fields = ["id",'application','titre',"text_input",'justification','created_at']
        read_only_fields = ["created_at",]