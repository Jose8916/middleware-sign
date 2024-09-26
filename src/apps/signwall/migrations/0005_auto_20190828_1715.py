# Generated by Django 2.2.3 on 2019-08-28 22:15

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signwall', '0004_auto_20190801_1738'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(null=True)),
                ('end_date', models.DateTimeField(null=True)),
                ('report_type', models.CharField(choices=[('sign-up-summary', 'Registros')], default='sign-up-summary', max_length=50, null=True)),
                ('site', models.CharField(max_length=20, null=True)),
                ('payload', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Request')),
                ('result', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Responce')),
                ('data', models.FileField(blank=True, null=True, upload_to='', verbose_name='Reporte')),
                ('records', models.IntegerField(blank=True, null=True, verbose_name='Número de registros')),
                ('data_loaded', models.NullBooleanField(verbose_name='Datos cargados')),
            ],
            options={
                'verbose_name': 'Reporte',
            },
        ),
        # migrations.DeleteModel(
        #     name='ArcReport',
        # ),
    ]
