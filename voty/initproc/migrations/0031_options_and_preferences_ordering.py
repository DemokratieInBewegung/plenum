# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2019-02-26 09:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('initproc', '0030_federal_state_levels'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='option',
            options={'ordering': ['index']},
        ),
        migrations.AlterModelOptions(
            name='preference',
            options={'ordering': ['option__index']},
        ),
    ]
