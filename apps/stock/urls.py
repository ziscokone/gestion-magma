from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('', views.ProduitListView.as_view(), name='produit_list'),
    path('inventaire.pdf', views.ProduitInventairePDFView.as_view(), name='produit_inventaire_pdf'),
    path('produits/ajouter/', views.ProduitCreateView.as_view(), name='produit_create'),
    path('produits/<int:pk>/', views.ProduitDetailView.as_view(), name='produit_detail'),
    path('produits/<int:pk>/modifier/', views.ProduitUpdateView.as_view(), name='produit_update'),
    path('produits/<int:pk>/supprimer/', views.ProduitDeleteView.as_view(), name='produit_delete'),

    path('mouvements/', views.MouvementListView.as_view(), name='mouvement_list'),
    path('mouvements/approvisionnement/', views.ApprovisionnementCreateView.as_view(), name='approvisionnement_create'),
    path('mouvements/vente/', views.VenteCreateView.as_view(), name='vente_create'),
    path('mouvements/vente/<int:pk>/confirmation/', views.VenteConfirmationView.as_view(), name='vente_confirmation'),
    path('mouvements/vente/<int:pk>/ticket.pdf', views.VenteTicketPDFView.as_view(), name='vente_ticket_pdf'),
    path('mouvements/ajustement/', views.AjustementCreateView.as_view(), name='ajustement_create'),

    path('fournisseurs/', views.FournisseurListView.as_view(), name='fournisseur_list'),
    path('fournisseurs/ajouter/', views.FournisseurCreateView.as_view(), name='fournisseur_create'),
    path('fournisseurs/<int:pk>/modifier/', views.FournisseurUpdateView.as_view(), name='fournisseur_update'),
    path('fournisseurs/<int:pk>/supprimer/', views.FournisseurDeleteView.as_view(), name='fournisseur_delete'),

    path('categories/', views.CategorieProduitListView.as_view(), name='categorie_produit_list'),
    path('categories/ajouter/', views.CategorieProduitCreateView.as_view(), name='categorie_produit_create'),
    path('categories/<int:pk>/modifier/', views.CategorieProduitUpdateView.as_view(), name='categorie_produit_update'),
    path('categories/<int:pk>/supprimer/', views.CategorieProduitDeleteView.as_view(), name='categorie_produit_delete'),
]
