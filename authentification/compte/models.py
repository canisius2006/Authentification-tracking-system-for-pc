from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings 
from django.utils import timezone
# Create your models here.
class User(AbstractUser):
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
    
    def __str__(self):
        return f"{self.username}"


class Session_activite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="sessions")
    jour = models.DateField(verbose_name='Jour',auto_now_add=True)
    heure_debut = models.TimeField(verbose_name='Heure de debut',auto_now_add=True)
    heure_fin = models.TimeField(verbose_name='Heure de fin',default=timezone.localtime().time())

    def __str__(self):
        return f"{self.user.username} le {self.jour} du {self.heure_debut} à {self.heure_fin}"

class Application(models.Model):
    session = models.ForeignKey(Session_activite,on_delete=models.CASCADE,related_name='applications')
    nom = models.CharField(max_length=25,verbose_name='Nom')
    heure_debut = models.TimeField(verbose_name='Heure de debut',auto_now_add=True)
    heure_fin = models.TimeField(verbose_name='Heure de fin',auto_now=True)

    def __str__(self):
        return self.nom

class Bad_action(models.Model):
    application = models.ForeignKey(Application,on_delete=models.CASCADE,related_name='bad_actions')
    titre = models.CharField(max_length=20,verbose_name='Titre',blank=True,null=True)
    text_input = models.TextField(verbose_name='Texte_brute')
    justification = models.TextField(verbose_name="Justification IA",)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre or "sans titre"

