# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-14 15:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('initproc', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='initiative',
            name='was_closed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='went_to_discussion_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='went_to_voting_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
