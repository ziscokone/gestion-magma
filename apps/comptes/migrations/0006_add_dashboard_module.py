from django.db import migrations

MODULE = {
    'cle': 'dashboard',
    'nom': 'Tableau de bord',
    'description': "Vue d'ensemble de l'activité, tous modules confondus",
    'icone': 'bi-speedometer2',
    'url_name': 'dashboard:accueil',
    'ordre': 0,
}


def insert_module(apps, schema_editor):
    Module = apps.get_model('comptes', 'Module')
    Module.objects.get_or_create(cle=MODULE['cle'], defaults=MODULE)


def remove_module(apps, schema_editor):
    Module = apps.get_model('comptes', 'Module')
    Module.objects.filter(cle=MODULE['cle']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0005_update_clients_module_url'),
    ]

    operations = [
        migrations.RunPython(insert_module, remove_module),
    ]
