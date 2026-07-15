from django.contrib import admin
from . import models 
from django.contrib.auth.admin import UserAdmin
# Register your models here.
admin.site.register(models.User,UserAdmin)
admin.site.register(models.Score)
admin.site.register(models.Session_activite)
admin.site.register(models.Application)
admin.site.register(models.Bad_action)