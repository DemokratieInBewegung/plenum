# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-07-08 12:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('initproc', '0015_initiative_variant_of'),
    ]

    operations = [
        migrations.AddField(
            model_name='vote',
            name='reason',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
