# -*- coding: utf-8 -*-
# 2018-08-17
from __future__ import unicode_literals

from django.db import migrations, models

def add_neweinordnung(apps, schema_editor):
    migrations.RunSQL('ALTER TABLE Initiative DROP CONSTRAINT einordnung_values;')
    migrations.RunSQL("""
    'ALTER TABLE Initiative ADD CONSTRAINT einordnung_values CHECK (
    einordnung in ('initiative', 'ao-aenderung', 'urabstimmung', 'plenumsentscheidung));'
    """)

def reverse_neweinordnung(apps, schema_editor):
    migrations.RunSQL('ALTER TABLE Initiative DROP CONSTRAINT einordnung_values;')
    migrations.RunSQL("""
    'ALTER TABLE Initiative ADD CONSTRAINT einordnung_values CHECK (
    einordnung in ('initiative', 'ao-aenderung', 'urabstimmung'));'
    """)

class Migration(migrations.Migration):

    dependencies = [
        ('initproc', '0027_merge_20180723_1813'),
    ]

    operations = [
        migrations.AlterField(
            model_name='initiative',
            name='einordnung',
            field=models.CharField(choices=[('initiative', 'Einzelinitiative'), ('ao-aenderung', 'AO-Änderung'), ('urabstimmung', 'Urabstimmung'), ('plenumsentscheidung', 'Plenumsentscheidung')], max_length=50),
        ),
        migrations.RunPython(add_neweinordnung,
                             reverse_code=reverse_neweinordnung),
    ]

