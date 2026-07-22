from django.contrib import admin
from .models import Etablissement


@admin.register(Etablissement)
class EtablissementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'telephone', 'email']
