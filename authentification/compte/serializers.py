from rest_framework import serializers 
from .models import Session_activite,Application,Bad_action
from django.contrib.auth import get_user_model 
from django.utils import timezone
from django.db.models import F 
import random
from datetime import datetime 

from drf_extra_fields.fields import HybridImageField #C'est cette bibliothèque qui nous permet de pouvoir faire l'enregistrement des photos même en base 64


User = get_user_model()


#La fonction pour pouvoir créer un matricule automatiquement 
def create_matricule():
    #La clé de vérification de notre côté est 97
    a = f'{int(str(datetime.now().year)[2:]):02d}'
    b = f'{datetime.now().month:02d}' 
    c = f'{random.randint(1,999):03d}'
    d = f'{(97 - ((int(a+b+c))%97)):02d}'
    e = str(a)+b+'U'+c+str(d)
    return e

def create_code():
    """Cette fonction va nous permettre de pouvoir créer un code de validation d'inscription, c'est à dire pour valider l'inscription de l'utilisateur"""
    return str(random.randint(112,999))

#Ce serializer sert à consulter ou modifier le profil.
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id','username','email','matricule','photo_de_profil','telephone','sexe','score','created_at','updated_at','first_name','last_name','activation_code']
        read_only_fields = ['id','created_at','updated_at']


#Celui-ci est utilisé uniquement lors de l'inscription.
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,min_length=8)
    photo_de_profil = HybridImageField(required=False, allow_null=True)
    class Meta:
        model = User 
        fields = ["username",'password','email','telephone','photo_de_profil','sexe','first_name','last_name']
        

    def create(self,validated_data):
        matricule = create_matricule()
        while User.objects.filter(matricule=matricule).exists():
            matricule = create_matricule()
        validated_data['matricule']=matricule
        validated_data['activation_code']=create_code()
        validated_data['is_active']=False

        telephone = validated_data.get('telephone')
        if not telephone or not telephone.strip():
            validated_data['telephone'] = None

        email = validated_data.get('email')
        if not email or not email.strip():
            validated_data['email'] = None

        return User.objects.create_user(**validated_data)
    
    def validate_telephone(self, value):
        if value == "" or value == " ":
            return None
        return value
    
    def validate_email(self, value):
        if value in ("", " ", None):
            return None

        value = value.strip().lower()

        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")

        return value

    


#cette classe pour l'enregistrement de la session utilisateur 
class SessionActiviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session_activite
        fields = ["id","jour","heure_debut","heure_fin"]
        read_only_fields = ['id',"jour","heure_debut","heure_fin"]

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Application
        fields = ['id','session','nom','heure_debut','heure_fin']
        read_only_fields = ['heure_debut','id',]

    def create(self,validated_data):
        application = Application.objects.filter(session=validated_data.get('session'),nom=validated_data.get('nom')).first()
        if application is not None:
            application.heure_fin = timezone.now().time()
            application.save(update_fields=['heure_fin'])
        else:
            application = Application.objects.create(**validated_data)
        session = application.session 
        session.heure_fin = timezone.now().time()
        session.save(update_fields=['heure_fin'])
        return application

class BadActionSerializer(serializers.ModelSerializer):
    application = serializers.CharField(write_only=True)
    class Meta:
        model = Bad_action
        fields = ["id",'application','titre',"text_input",'justification','created_at']
        read_only_fields = ["created_at",'id']
    def create(self,validated_data):
        action = Bad_action.objects.filter(application=validated_data.get('application'),titre=validated_data.get('titre'),text_input=validated_data.get('text_input')).first()
        if action is not None:
            pass
        else:
            action = Bad_action.objects.create(**validated_data)
            user = action.application.session.user 
            user.score  = F('score') - 2

        user = action.application.session.user 
        session = action.application.session
        application = action.application 
        #Ici, on agit sur les heures de fin de chaque champ 
        session.heure_fin = timezone.now().time()
        application.heure_fin = timezone.now().time()
       
        #Ici, il faut faire l'enregistrement
        session.save(update_fields=['heure_fin'])
        application.save(update_fields=['heure_fin'])
        user.save(update_fields=['score'])
        return action 


class ActivationCompteSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    activation_code = serializers.CharField(max_length=3)




