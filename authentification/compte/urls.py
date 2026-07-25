from rest_framework.routers import DefaultRouter 
from .views import UserModelView,RegisterApiView,SessionActiviteModelView,ApplicationModelView,Bad_actionModelView 
from django.urls import path,include
from . import views
#Définition des views pour nos modelsview set
router = DefaultRouter()
router.register(r'users',UserModelView,basename='users')#Pour checker tous les utilisateurs
router.register(r'session',SessionActiviteModelView,basename='session')
router.register(r'application',ApplicationModelView,basename='application')
router.register(r'bad_action',Bad_actionModelView,basename='bad_action')

urlpatterns = [
    path('',views.accueil),
    path('inscription',RegisterApiView.as_view(),name='inscription'),
    path('',include(router.urls))
]