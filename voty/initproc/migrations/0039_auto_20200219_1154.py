# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2020-02-19 10:54
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('initproc', '0038_remove_closed_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=80, unique=True)),
                ('motivation', models.TextField(blank=True, max_length=1000)),
                ('level', models.CharField(choices=[('Bund', 'Bund'), ('Baden-Württemberg', 'Baden-Württemberg'), ('Bayern', 'Bayern'), ('Berlin', 'Berlin'), ('Brandenburg', 'Brandenburg'), ('Bremen', 'Bremen'), ('Hamburg', 'Hamburg'), ('Hessen', 'Hessen'), ('Mecklenburg-Vorpommern', 'Mecklenburg-Vorpommern'), ('Niedersachsen', 'Niedersachsen'), ('Nordrhein-Westfalen', 'Nordrhein-Westfalen'), ('Rheinland-Pfalz', 'Rheinland-Pfalz'), ('Saarland', 'Saarland'), ('Sachsen', 'Sachsen'), ('Sachsen-Anhalt', 'Sachsen-Anhalt'), ('Schleswig-Holstein', 'Schleswig-Holstein'), ('Thüringen', 'Thüringen')], default='Bund', max_length=50)),
                ('createdate', models.DateTimeField(auto_now_add=True)),
                ('changedate', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('p', 'preparation'), ('i', 'review'), ('s', 'seeking support'), ('d', 'in discussion'), ('m', 'in discussion, final review'), ('v', 'is being voted on'), ('x', 'overcome veto'), ('c', 'was completed')], default='p', max_length=1)),
                ('went_to_review_at', models.DateField(blank=True, null=True)),
                ('went_to_seeking_support_at', models.DateField(blank=True, null=True)),
                ('went_to_discussion_at', models.DateField(blank=True, null=True)),
                ('went_to_final_review_at', models.DateField(blank=True, null=True)),
                ('went_to_voting_at', models.DateField(blank=True, null=True)),
                ('went_to_veto_phase_at', models.DateField(blank=True, null=True)),
                ('was_closed_at', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='IssueSupportersQuorum',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('value', models.IntegerField(null=0)),
            ],
        ),
        migrations.CreateModel(
            name='IssueVotersQuorum',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('value', models.IntegerField(null=0)),
            ],
        ),
        migrations.CreateModel(
            name='Solution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=80)),
                ('description', models.TextField(blank=True, max_length=1000)),
                ('budget', models.IntegerField(null=0)),
                ('createdate', models.DateTimeField(auto_now_add=True)),
                ('changedate', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('d', 'in discussion'), ('a', 'review passed'), ('r', 'rejected by review')], default='d', max_length=1)),
                ('passed_review_at', models.DateTimeField(blank=True, null=True)),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solutions', to='initproc.Issue')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Veto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('createdate', models.DateTimeField(auto_now_add=True)),
                ('reason', models.TextField(max_length=1000)),
                ('solution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refusing', to='initproc.Solution')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='resistance',
            name='solution',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rating', to='initproc.Solution'),
        ),
        migrations.AlterField(
            model_name='contra',
            name='initiative',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contras', to='initproc.Initiative'),
        ),
        migrations.AlterField(
            model_name='moderation',
            name='initiative',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='moderations', to='initproc.Initiative'),
        ),
        migrations.AlterField(
            model_name='pro',
            name='initiative',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pros', to='initproc.Initiative'),
        ),
        migrations.AlterField(
            model_name='proposal',
            name='initiative',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='proposals', to='initproc.Initiative'),
        ),
        migrations.AlterField(
            model_name='question',
            name='initiative',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='initproc.Initiative'),
        ),
        migrations.AlterField(
            model_name='resistance',
            name='contribution',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='resistances', to='initproc.Initiative'),
        ),
        migrations.AlterField(
            model_name='supporter',
            name='initiative',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supporting', to='initproc.Initiative'),
        ),
        migrations.AlterUniqueTogether(
            name='resistance',
            unique_together=set([('user', 'contribution', 'solution')]),
        ),
        migrations.AddField(
            model_name='contra',
            name='solution',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contraslist', to='initproc.Solution'),
        ),
        migrations.AddField(
            model_name='moderation',
            name='issue',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='issuemoderations', to='initproc.Issue'),
        ),
        migrations.AddField(
            model_name='moderation',
            name='solution',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='moderationslist', to='initproc.Solution'),
        ),
        migrations.AddField(
            model_name='pro',
            name='solution',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='proslist', to='initproc.Solution'),
        ),
        migrations.AddField(
            model_name='proposal',
            name='solution',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='proposalslist', to='initproc.Solution'),
        ),
        migrations.AddField(
            model_name='question',
            name='solution',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questionslist', to='initproc.Solution'),
        ),
        migrations.AddField(
            model_name='supporter',
            name='issue',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supporters', to='initproc.Issue'),
        ),
        migrations.AlterUniqueTogether(
            name='supporter',
            unique_together=set([('user', 'initiative', 'issue')]),
        ),
        migrations.AlterUniqueTogether(
            name='veto',
            unique_together=set([('user', 'solution')]),
        ),
        migrations.AlterUniqueTogether(
            name='solution',
            unique_together=set([('issue', 'title')]),
        ),
    ]
