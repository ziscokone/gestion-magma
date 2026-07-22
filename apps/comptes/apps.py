from django.apps import AppConfig


class ComptesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.comptes'
    label = 'comptes'
    verbose_name = 'Comptes utilisateurs'
