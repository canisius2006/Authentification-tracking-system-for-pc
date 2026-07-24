from rest_framework import serializers 
from .models import Score,Session_activite,Application,Bad_action
from django.contrib.auth import get_user_model 
User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email','matricule','password','photo_de_profil','telephone','sexe']
