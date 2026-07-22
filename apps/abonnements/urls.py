from django.urls import path
from . import views

app_name = 'abonnements'

urlpatterns = [
    path('', views.AbonnementListView.as_view(), name='abonnement_list'),
    path('nouveau/', views.AbonnementCreateView.as_view(), name='abonnement_create'),
    path('relances/', views.AbonnementRelanceListView.as_view(), name='relance_list'),
    path('<int:pk>/relance/', views.AbonnementRelanceToggleView.as_view(), name='relance_toggle'),

    path('types/', views.TypeAbonnementListView.as_view(), name='type_abonnement_list'),
    path('types/ajouter/', views.TypeAbonnementCreateView.as_view(), name='type_abonnement_create'),
    path('types/<int:pk>/modifier/', views.TypeAbonnementUpdateView.as_view(), name='type_abonnement_update'),
    path('types/<int:pk>/supprimer/', views.TypeAbonnementDeleteView.as_view(), name='type_abonnement_delete'),

    path('<int:pk>/', views.AbonnementDetailView.as_view(), name='abonnement_detail'),
    path('<int:pk>/renouveler/', views.AbonnementRenewView.as_view(), name='abonnement_renew'),
    path('<int:pk>/paiement/', views.AbonnementPaiementCreateView.as_view(), name='abonnement_paiement_create'),
    path('<int:pk>/fiche.pdf', views.AbonnementFichePDFView.as_view(), name='abonnement_fiche_pdf'),
    path('<int:pk>/paiement/<int:paiement_pk>/recu.pdf', views.PaiementRecuPDFView.as_view(), name='paiement_recu_pdf'),
]
