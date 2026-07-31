from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.SeanceListView.as_view(), name='seance_list'),
    path('nouvelle/', views.SeanceCreateView.as_view(), name='seance_create'),
    path('api/rechercher-client/', views.rechercher_client, name='rechercher_client'),
    path('api/suggerer-clients/', views.suggerer_clients, name='suggerer_clients'),
    path('liste/', views.ClientListView.as_view(), name='client_list'),

    path('types-prestation/', views.TypePrestationListView.as_view(), name='type_prestation_list'),
    path('types-prestation/ajouter/', views.TypePrestationCreateView.as_view(), name='type_prestation_create'),
    path('types-prestation/<int:pk>/modifier/', views.TypePrestationUpdateView.as_view(), name='type_prestation_update'),
    path('types-prestation/<int:pk>/supprimer/', views.TypePrestationDeleteView.as_view(), name='type_prestation_delete'),

    path('objectifs/', views.ObjectifSportifListView.as_view(), name='objectif_sportif_list'),
    path('objectifs/ajouter/', views.ObjectifSportifCreateView.as_view(), name='objectif_sportif_create'),
    path('objectifs/<int:pk>/modifier/', views.ObjectifSportifUpdateView.as_view(), name='objectif_sportif_update'),
    path('objectifs/<int:pk>/supprimer/', views.ObjectifSportifDeleteView.as_view(), name='objectif_sportif_delete'),

    path('<uuid:public_id>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('<uuid:public_id>/modifier/', views.ClientUpdateView.as_view(), name='client_update'),
]
