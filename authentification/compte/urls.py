from rest_framework.routers import DefaultRouter 
from .views import UserModelView,RegisterApiView,SessionActiviteModelView,ApplicationModelView,Bad_actionModelView,ValiderInscriptionApiView,ListInscriptionPendingView
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
    path('check-user/',views.CheckUsernameApiView.as_view(),name='checkusername'),
    path('validation-inscription/',ValiderInscriptionApiView.as_view(),name='validation-inscription'),
    path('liste-pending/',ListInscriptionPendingView.as_view(),name='liste-pending'),
    
    path('',include(router.urls))
]