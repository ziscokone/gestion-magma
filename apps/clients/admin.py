from django.contrib import admin
from .models import Client, Quartier, Seance, TypePrestation


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'telephone', 'quartier', 'nombre_seances']
    list_filter = ['quartier']
    search_fields = ['nom_complet', 'telephone']


@admin.register(Quartier)
class QuartierAdmin(admin.ModelAdmin):
    list_display = ['nom', 'actif']
    list_editable = ['actif']


@admin.register(TypePrestation)
class TypePrestationAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prix', 'ordre', 'actif']
    list_editable = ['ordre', 'actif']


@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ['client', 'date', 'type_prestation', 'montant', 'statut_paiement']
    list_filter = ['type_prestation', 'statut_paiement', 'mode_paiement']
