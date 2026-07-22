from django.contrib import admin
from .models import TypeAbonnement, Abonnement, PaiementAbonnement


@admin.register(TypeAbonnement)
class TypeAbonnementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prix', 'duree_jours', 'ordre', 'actif']
    list_editable = ['ordre', 'actif']


class PaiementAbonnementInline(admin.TabularInline):
    model = PaiementAbonnement
    extra = 0


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ['client', 'type_abonnement', 'date_debut', 'date_fin', 'montant', 'statut_paiement_display']
    list_filter = ['type_abonnement']
    inlines = [PaiementAbonnementInline]

    def statut_paiement_display(self, obj):
        return obj.statut_paiement_display
    statut_paiement_display.short_description = "Statut du paiement"


@admin.register(PaiementAbonnement)
class PaiementAbonnementAdmin(admin.ModelAdmin):
    list_display = ['abonnement', 'montant', 'date', 'mode_paiement']
    list_filter = ['mode_paiement']
