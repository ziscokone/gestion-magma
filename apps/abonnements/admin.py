from django.contrib import admin
from .models import TypeAbonnement, Abonnement


@admin.register(TypeAbonnement)
class TypeAbonnementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prix', 'duree_jours', 'ordre', 'actif']
    list_editable = ['ordre', 'actif']


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ['client', 'type_abonnement', 'date_debut', 'date_fin', 'montant']
    list_filter = ['type_abonnement']
