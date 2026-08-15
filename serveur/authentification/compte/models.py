from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings 
from django.utils import timezone
# Create your models here.
class User(AbstractUser):
    email = models.EmailField(null=True,blank=True,default=None)
    matricule = models.CharField(verbose_name='Matricule',unique=True,max_length=20)
    photo_de_profil = models.ImageField(verbose_name='Photo de Profil',upload_to='Profil/',blank=True,null=True)
    telephone = models.CharField(verbose_name='Numéro de Telephone',max_length=20,unique=True,blank=True,null=True)
    class Sexe(models.TextChoices):
        HOMME = ('H','HOMME')
        FEMME = ('F','FEMME')
    sexe = models.CharField(verbose_name='Sexe',choices=Sexe.choices,blank=True,null=True,max_length=1)
    score = models.IntegerField(verbose_name='score',default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activation_code = models.CharField(max_length=3,blank=True,null=True)
    
    def __str__(self):
        return f"{self.username}"

def heure_actuelle():
    """Cette fonction va nous permettre d'avoir l'heure actuelle """
    return timezone.localtime().time()
def jour_actuelle():
    return timezone.localtime().date()

class Session_activite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="sessions")
    jour = models.DateField(verbose_name='Jour',default=jour_actuelle)
    pc = models.CharField(max_length=255,verbose_name='Nom du pc')
    heure_debut = models.TimeField(verbose_name='Heure de debut',default=heure_actuelle)
    heure_fin = models.TimeField(verbose_name='Heure de fin',default=heure_actuelle)


    def __str__(self):
        return f"{self.user.username} le {self.jour} du {self.heure_debut} à {self.heure_fin}"

class Application(models.Model):
    session = models.ForeignKey(Session_activite,on_delete=models.CASCADE,related_name='applications')
    nom = models.CharField(max_length=255,verbose_name='Nom')
    heure_debut = models.TimeField(verbose_name='Heure de debut',default=heure_actuelle)
    heure_fin = models.TimeField(verbose_name='Heure de fin',default=heure_actuelle)

    def __str__(self):
        return self.nom

class Bad_action(models.Model):
    application = models.ForeignKey(Application,on_delete=models.CASCADE,related_name='bad_actions')
    titre = models.CharField(max_length=255,verbose_name='Titre',blank=True,null=True)
    text_input = models.TextField(verbose_name='Texte_brute')
    justification = models.TextField(verbose_name="Justification IA",)
    count = models.IntegerField(verbose_name='Nombre de fois commis',default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre or "sans titre"


