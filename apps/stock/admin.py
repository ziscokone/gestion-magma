from django.contrib import admin
from .models import CategorieProduit, Fournisseur, Produit, MouvementStock


@admin.register(CategorieProduit)
class CategorieProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'actif']


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'telephone', 'actif']
    search_fields = ['nom', 'telephone']


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'categorie', 'prix_achat', 'prix_vente', 'seuil_alerte', 'actif']
    list_filter = ['categorie', 'actif']


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ['produit', 'type_mouvement', 'quantite', 'date', 'motif']
    list_filter = ['type_mouvement', 'motif']
