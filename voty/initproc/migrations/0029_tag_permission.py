from django.contrib.auth.models import Group, Permission
from django.db import migrations

def init_tag_permission(apps, schema_editor):
    Group.objects.get(name='Prüfungsteam').permissions.add(Permission.objects.get(content_type__app_label='initproc', codename='change_tag'))
    print ('... added permission for group "Prüfungsteam" to change tags')

def reverse_tag_permission(apps, schema_editor):
    Group.objects.get(name='Prüfungsteam').permissions.remove(Permission.objects.get(content_type__app_label='initproc', codename='change_tag'))
    print ('... removed permission for group "Prüfungsteam" to change tags')


class Migration(migrations.Migration):

    dependencies = [
        ('initproc', '0023_auto_20171007_1601'),
    ]

    operations = [
        migrations.RunPython(init_tag_permission,
                             reverse_code=reverse_tag_permission),
    ]
