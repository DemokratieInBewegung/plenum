# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2019-03-20 17:37
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('initproc', '0035_new_topic_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='Resistance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('changed_at', models.DateTimeField(auto_now=True)),
                ('value', models.IntegerField()),
                ('reason', models.CharField(blank=True, max_length=100)),
                ('contribution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resistances', to='initproc.Initiative')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='resistance',
            unique_together=set([('user', 'contribution')]),
        ),
    ]
