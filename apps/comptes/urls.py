from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'comptes'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='comptes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('utilisateurs/', views.UtilisateurListView.as_view(), name='utilisateur_list'),
    path('utilisateurs/ajouter/', views.UtilisateurCreateView.as_view(), name='utilisateur_create'),
    path('utilisateurs/<int:pk>/modifier/', views.UtilisateurUpdateView.as_view(), name='utilisateur_update'),
    path('utilisateurs/<int:pk>/supprimer/', views.UtilisateurDeleteView.as_view(), name='utilisateur_delete'),
    path('utilisateurs/<int:pk>/modules/', views.ModulesUtilisateurView.as_view(), name='utilisateur_modules'),
]
