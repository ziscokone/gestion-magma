from django.db import migrations

MODULES = [
    {'cle': 'clients',     'nom': 'Clients & Séances', 'description': 'Séances, prestations et paiements',        'icone': 'bi-person-walking',  'url_name': 'clients:client_list',        'ordre': 1},
    {'cle': 'abonnements', 'nom': 'Abonnements',        'description': 'Souscriptions et suivi des renouvellements', 'icone': 'bi-card-checklist',  'url_name': 'abonnements:abonnement_list', 'ordre': 2},
    {'cle': 'stock',       'nom': 'Gestion de Stock',   'description': 'Produits, mouvements et seuils d\'alerte',   'icone': 'bi-box-seam',        'url_name': 'stock:produit_list',          'ordre': 3},
    {'cle': 'budget',      'nom': 'Gestion Budgétaire', 'description': 'Recettes, dépenses et solde de caisse',      'icone': 'bi-cash-coin',        'url_name': 'budget:operation_list',       'ordre': 4},
    {'cle': 'comptes',     'nom': 'Utilisateurs & Accès', 'description': 'Comptes utilisateurs et droits d\'accès',   'icone': 'bi-people-fill',      'url_name': 'comptes:utilisateur_list',    'ordre': 5},
]


def insert_modules(apps, schema_editor):
    Module = apps.get_model('comptes', 'Module')
    for data in MODULES:
        Module.objects.get_or_create(cle=data['cle'], defaults=data)


def remove_modules(apps, schema_editor):
    Module = apps.get_model('comptes', 'Module')
    Module.objects.filter(cle__in=[m['cle'] for m in MODULES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insert_modules, remove_modules),
    ]
