from django.contrib import admin
from .models import CategorieCharge, OperationBudget


@admin.register(CategorieCharge)
class CategorieChargeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'actif']


@admin.register(OperationBudget)
class OperationBudgetAdmin(admin.ModelAdmin):
    list_display = ['date', 'type_operation', 'categorie', 'montant', 'est_automatique']
    list_filter = ['type_operation', 'categorie']
