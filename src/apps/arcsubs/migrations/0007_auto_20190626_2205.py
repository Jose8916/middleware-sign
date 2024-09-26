# Generated by Django 2.2 on 2019-06-27 03:05

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0006_arcuser_first_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='MppUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField(max_length=128, null=True, unique=True, verbose_name='Email')),
                ('csv_profile', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('mpp_profile', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('arc_profile', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('status', models.CharField(blank=True, choices=[('UNKNOWN', 'Desconocido'), ('PENDING', 'Usuario inactivo'), ('IN_PROCESS', 'Contraseña pendiente'), ('MIGRATED', 'Migración completa')], default=None, max_length=128, null=True, verbose_name='Estado')),
            ],
            options={
                'verbose_name': 'Usuario de migración',
                'verbose_name_plural': 'ARC estado de usuarios',
                'db_table': 'ecoid_migrateuser',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MppUserLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField(db_column='us_email', db_index=True, max_length=128, null=True, verbose_name='Email')),
                ('domain', models.CharField(max_length=128, null=True, verbose_name='Domain')),
                ('date_register', models.DateTimeField(blank=True, null=True, verbose_name='Date register')),
                ('date_edition', models.DateTimeField(blank=True, null=True, verbose_name='Date edition')),
                ('mpp_account_id', models.CharField(max_length=128, null=True, verbose_name='Mpp Account')),
                ('arc_account_id', models.CharField(blank=True, max_length=128, null=True, verbose_name='Arc Account')),
                ('type', models.CharField(max_length=32, null=True, verbose_name='Type')),
                ('content', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('ip', models.CharField(max_length=32, null=True, verbose_name='IP')),
                ('referer', models.CharField(max_length=350, null=True, verbose_name='Referer')),
                ('user_agent', models.CharField(max_length=350, null=True, verbose_name='User Agent')),
                ('origin_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('state', models.BooleanField(default=True, verbose_name='State')),
            ],
            options={
                'verbose_name': 'Reactivación de sesion',
                'verbose_name_plural': 'ARC pasos de reactivación',
                'db_table': 'ecoid_usercredentials',
                'managed': False,
            },
        ),
        migrations.AlterModelOptions(
            name='arcuser',
            options={'verbose_name': 'Usuario de ARC', 'verbose_name_plural': 'Usuarios de ARC'},
        ),
        migrations.AddField(
            model_name='arcuser',
            name='fist_login',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Primer login'),
        ),
        migrations.AddField(
            model_name='arcuser',
            name='from_mpp',
            field=models.NullBooleanField(verbose_name='Migrado de MPP'),
        ),
        migrations.AlterField(
            model_name='arcuser',
            name='domain',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Domain'),
        ),
        migrations.AlterField(
            model_name='arcuser',
            name='first_profile',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='First profile'),
        ),
    ]