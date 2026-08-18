from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


# ============================================================
# ACTION : remettre le score des utilisateurs sélectionnés à 20
# ============================================================

@admin.action(description="Remettre le score à 20")
def remettre_score_a_20(modeladmin, request, queryset):
    nombre_modifie = queryset.update(score=20)

    modeladmin.message_user(
        request,
        f"{nombre_modifie} utilisateur(s) ont été remis à 20."
    )


# ============================================================
# ADMINISTRATION DU USER PERSONNALISÉ
# ============================================================

class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            "Informations complémentaires",
            {
                "fields": (
                    "matricule",
                    "photo_de_profil",
                    "telephone",
                    "sexe",
                    "score",
                    "activation_code",
                )
            },
        ),
    )

    actions = [
        remettre_score_a_20,
    ]


# ============================================================
# ENREGISTREMENT DES MODÈLES
# ============================================================

admin.site.register(models.User, CustomUserAdmin)

admin.site.register(models.Session_activite)
admin.site.register(models.Application)
admin.site.register(models.Bad_action)