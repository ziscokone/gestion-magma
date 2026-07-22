from django.db import migrations

REMAP = {
    'admin': 'super_admin',
    'employe': 'utilisateur',
}


def remap_forward(apps, schema_editor):
    Utilisateur = apps.get_model('comptes', 'Utilisateur')
    for old_role, new_role in REMAP.items():
        Utilisateur.objects.filter(role=old_role).update(role=new_role)


def remap_backward(apps, schema_editor):
    Utilisateur = apps.get_model('comptes', 'Utilisateur')
    for old_role, new_role in REMAP.items():
        Utilisateur.objects.filter(role=new_role).update(role=old_role)


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0003_alter_utilisateur_role'),
    ]

    operations = [
        migrations.RunPython(remap_forward, remap_backward),
    ]
