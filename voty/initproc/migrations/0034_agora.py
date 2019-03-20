# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2019-02-28 07:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('initproc', '0033_municipal_election_levels'),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('likes_count', models.IntegerField(default=0)),
                ('comments_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('changed_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=140)),
                ('text', models.CharField(max_length=1024)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('topic', models.TextField(blank=True)),
            ],
        ),
        migrations.AlterField(
            model_name='initiative',
            name='einordnung',
            field=models.CharField(choices=[('initiative', 'Einzelinitiative'), ('ao-aenderung', 'AO-Änderung'), ('urabstimmung', 'Urabstimmung'), ('plenumsentscheidung', 'Plenumsentscheidung'), ('plenumsabwaegung', 'Plenumsabwägung'), ('beitrag', 'Beitrag')], max_length=50),
        ),
        migrations.AddField(
            model_name='question',
            name='initiative',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='initproc.Initiative'),
        ),
        migrations.AddField(
            model_name='question',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='initiative',
            name='topic',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='initproc.Topic'),
        ),
    ]
