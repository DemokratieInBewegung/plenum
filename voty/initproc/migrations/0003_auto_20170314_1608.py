# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-14 16:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('initproc', '0002_auto_20170314_1534'),
    ]

    operations = [
        migrations.RenameField(
            model_name='initiative',
            old_name='einordgnung',
            new_name='einordnung',
        ),
        migrations.AlterField(
            model_name='initiative',
            name='title',
            field=models.CharField(max_length=80),
        ),
    ]
