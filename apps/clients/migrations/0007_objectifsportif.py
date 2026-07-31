from django.db import migrations, models
import django.db.models.deletion


# Anciennes valeurs (cle, nom) du champ `objectif` figé en choix — reprises
# ici telles quelles pour ne rien perdre, migrées ensuite vers ObjectifSportif.
ANCIENS_OBJECTIFS = [
    ('perte_poids', 'Perte de poids'),
    ('prise_masse', 'Prise de masse musculaire'),
    ('remise_forme', 'Remise en forme / Bien-être'),
    ('preparation_sportive', 'Préparation sportive'),
]


def seeder_et_migrer_objectifs(apps, schema_editor):
    ObjectifSportif = apps.get_model('clients', 'ObjectifSportif')
    Client = apps.get_model('clients', 'Client')

    objectifs_par_cle = {}
    for cle, nom in ANCIENS_OBJECTIFS:
        objectif, _ = ObjectifSportif.objects.get_or_create(cle=cle, defaults={'nom': nom})
        objectifs_par_cle[cle] = objectif

    for client in Client.objects.exclude(objectif='').exclude(objectif__isnull=True):
        objectif = objectifs_par_cle.get(client.objectif)
        if objectif:
            client.objectif_fk = objectif
            client.save(update_fields=['objectif_fk'])


def revenir_en_arriere(apps, schema_editor):
    """Pas de retour arrière automatisé : les objectifs restent en base même
    si la migration est annulée, ce qui n'est pas destructeur."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_client_indicatif_pays'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObjectifSportif',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cle', models.SlugField(blank=True, max_length=50, null=True, unique=True, verbose_name='Clé technique')),
                ('nom', models.CharField(max_length=100, verbose_name='Nom')),
                ('actif', models.BooleanField(default=True, verbose_name='Actif')),
            ],
            options={
                'verbose_name': 'Objectif sportif',
                'verbose_name_plural': 'Objectifs sportifs',
                'ordering': ['nom'],
            },
        ),
        migrations.AddField(
            model_name='client',
            name='objectif_fk',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='clients', to='clients.objectifsportif', verbose_name='Objectif sportif',
            ),
        ),
        migrations.RunPython(seeder_et_migrer_objectifs, revenir_en_arriere),
        migrations.RemoveField(
            model_name='client',
            name='objectif',
        ),
        migrations.RenameField(
            model_name='client',
            old_name='objectif_fk',
            new_name='objectif',
        ),
    ]
