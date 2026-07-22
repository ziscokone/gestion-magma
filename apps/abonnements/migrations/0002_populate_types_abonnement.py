from django.db import migrations

TYPES_SEED = [
    {'cle': 'standard', 'nom': 'Abonnement standard', 'prix': 15000, 'duree_jours': 30, 'ordre': 1},
    {'cle': 'tapis', 'nom': 'Abonnement + tapis de course', 'prix': 20000, 'duree_jours': 30, 'ordre': 2},
    {'cle': 'vip', 'nom': 'Abonnement VIP (toutes machines)', 'prix': 25000, 'duree_jours': 30, 'ordre': 3},
]


def seed_types(apps, schema_editor):
    TypeAbonnement = apps.get_model('abonnements', 'TypeAbonnement')
    for data in TYPES_SEED:
        TypeAbonnement.objects.get_or_create(cle=data['cle'], defaults=data)


def remove_types(apps, schema_editor):
    TypeAbonnement = apps.get_model('abonnements', 'TypeAbonnement')
    TypeAbonnement.objects.filter(cle__in=[t['cle'] for t in TYPES_SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('abonnements', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_types, remove_types),
    ]
