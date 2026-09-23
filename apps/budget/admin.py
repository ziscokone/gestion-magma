from django.contrib import admin
from .models import CategorieCharge, OperationBudget


@admin.register(CategorieCharge)
class CategorieChargeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'actif']


@admin.register(OperationBudget)
class OperationBudgetAdmin(admin.ModelAdmin):
    """Pas de suppression, même depuis l'admin Django : une opération de
    caisse s'annule (voir le journal dans l'application), elle ne s'efface
    jamais — traçabilité comptable."""
    list_display = ['date', 'type_operation', 'categorie', 'montant', 'est_automatique', 'annulee']
    list_filter = ['type_operation', 'categorie', 'annulee']

    def has_delete_permission(self, request, obj=None):
        return False
