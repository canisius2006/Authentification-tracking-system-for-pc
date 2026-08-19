"""
URL configuration for authentification project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings 
from django.conf.urls.static import static 
from rest_framework_simplejwt.views import (
    TokenObtainPairView, #Nous allons utiliser une autre view adapté avec du rate limit appliqué 
    TokenRefreshView,
)

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from compte import views

urlpatterns = [
    path('',views.accueil),
    path('api/token/', views.ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('api/',include('compte.urls')),
    # Génère le fichier de schéma OpenAPI au format YAML/JSON
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Interface Swagger UI interactive (tester les requêtes en direct)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Alternative : Interface Redoc
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('pending/',views.pending,name='pending'),
    path('test/',views.ma_vue),
    path('profil/<str:valeur>/',views.profil,),
    path('extinction/',views.extinction),
    path('guide/',views.guide,name='guide'),
    path('termes/',views.termes,name='termes'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('session/',views.session,name='session'),
    path('session_detail/',views.session_detail,name='session_detail'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if not settings.DEBUG:
    from django.views.static import serve
    from django.urls import re_path
    
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
