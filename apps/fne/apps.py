from django.apps import AppConfig


class FneConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fne'
    label = 'fne'
    verbose_name = "Facturation Normalisée Électronique (FNE)"
