# Generated by Django 2.2 on 2019-06-14 23:40

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0005_arcuser_domain'),
    ]

    operations = [
        migrations.AddField(
            model_name='arcuser',
            name='first_profile',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Profile'),
        ),
    ]
