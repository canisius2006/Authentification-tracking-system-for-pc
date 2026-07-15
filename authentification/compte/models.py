from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    matricule = models.CharField(verbose_name='Matricule',primary_key=True,max_length=20)
    photo_de_profil = models.ImageField(verbose_name='Photo de Profil',upload_to='Profil/',blank=True,null=True)
    telephone = models.CharField(verbose_name='Numéro de Telephone',max_length=20,unique=True,blank=True,null=True)
    class Sexe(models.TextChoices):
        HOMME = ('H','HOMME')
        FEMME = ('F','FEMME')
    sexe = models.CharField(verbose_name='Sexe',choices=Sexe.choices,blank=True,null=True,max_length=1)

class Score(models.Model):
    matricule = models.ForeignKey(User,on_delete=models.CASCADE)
    valeur = models.IntegerField(verbose_name='score',default=20)

class Session_activite(models.Model):
    matricule = models.ForeignKey(User,on_delete=models.CASCADE)
    jour = models.DateField(verbose_name='Jour',auto_now_add=True)
    heure_debut = models.TimeField(verbose_name='Heure de debut',auto_now_add=True)
    heure_fin = models.TimeField(verbose_name='Heure de fin',auto_now=True)

class Application(models.Model):
    id_session = models.ForeignKey(Session_activite,on_delete=models.CASCADE)
    nom = models.CharField(max_length=25,verbose_name='Nom')
    heure_debut = models.TimeField(verbose_name='Heure de debut',auto_now_add=True)
    heure_fin = models.TimeField(verbose_name='Heure de fin',auto_now=True)

class Bad_action(models.Model):
    id_application = models.ForeignKey(Application,on_delete=models.CASCADE)
    titre = models.CharField(max_length=20,verbose_name='Titre',blank=True,null=True)
    text_input = models.TextField(verbose_name='Texte_brute')
    justification = models.TextField(verbose_name="Justification IA",)

