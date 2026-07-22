from django.db import migrations


def update_url(apps, schema_editor):
    Module = apps.get_model('comptes', 'Module')
    Module.objects.filter(cle='clients').update(url_name='clients:seance_list')


def revert_url(apps, schema_editor):
    Module = apps.get_model('comptes', 'Module')
    Module.objects.filter(cle='clients').update(url_name='clients:client_list')


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0004_remap_old_roles'),
    ]

    operations = [
        migrations.RunPython(update_url, revert_url),
    ]
