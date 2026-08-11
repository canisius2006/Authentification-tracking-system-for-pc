from django.contrib import admin
from . import models 
from django.contrib.auth.admin import UserAdmin

# Register your models here.

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informations complémentaires', {
            'fields': ('matricule', 'photo_de_profil', 'telephone', 'sexe', 'score','activation_code')
        }),
    )
    

admin.site.register(models.User, CustomUserAdmin)

admin.site.register(models.Session_activite)
admin.site.register(models.Application)
admin.site.register(models.Bad_action)