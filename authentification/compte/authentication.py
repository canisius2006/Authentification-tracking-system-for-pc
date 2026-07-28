from django.contrib.auth import get_user_model 
from django.contrib.auth.backends import ModelBackend 
from django.db.models import Q 

User = get_user_model()


class MultifieldAuthBackend(ModelBackend):
    def authenticate(self, request, username = ..., password = ..., **kwargs):
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(
                Q(username=username)|
                Q(email=username)|
                Q(matricule=username)|
                Q(telephone=username)
            )
        except User.DoesNotExist:
            return None 
        except User.MultipleObjectsReturned:
            return None 
        if user.check_password(password) and self.user_can_authenticate(user):
            return user 

        return None