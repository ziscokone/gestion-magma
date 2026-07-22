from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Module


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    model = Utilisateur
    list_display = ['username', 'nom_complet', 'role', 'actif', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Informations MAGMA', {'fields': ('nom_complet', 'telephone', 'role', 'actif', 'modules_autorises')}),
    )


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['nom', 'cle', 'ordre', 'actif']
    list_editable = ['ordre', 'actif']
