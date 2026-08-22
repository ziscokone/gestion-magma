from django.contrib import admin

from .models import CertificationFNE


@admin.register(CertificationFNE)
class CertificationFNEAdmin(admin.ModelAdmin):
    """Lecture seule : le journal ne doit jamais être modifié à la main,
    seulement consulté (l'écran de gestion dédié permet la relance)."""
    list_display = ['statut', 'reference_fne', 'content_type', 'object_id', 'date_tentative']
    list_filter = ['statut', 'content_type']
    readonly_fields = [f.name for f in CertificationFNE._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
