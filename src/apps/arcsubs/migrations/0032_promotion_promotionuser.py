# Generated by Django 2.2.9 on 2020-02-13 15:36

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0031_auto_20200127_1531'),
    ]

    operations = [
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado')),
                ('last_updated', models.DateTimeField(auto_now=True, null=True, verbose_name='Modificado')),
                ('name', models.CharField(blank=True, max_length=120, null=True, verbose_name='Nombre')),
            ],
            options={
                'verbose_name': 'Promocion',
                'verbose_name_plural': '[ARC] Promociones',
            },
        ),
        migrations.CreateModel(
            name='PromotionUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado')),
                ('last_updated', models.DateTimeField(auto_now=True, null=True, verbose_name='Modificado')),
                ('profile', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Profile')),
                ('state', models.IntegerField(blank=True, null=True, verbose_name='state user')),
                ('arc_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='user_promotion', to='arcsubs.ArcUser', verbose_name='Usuario')),
                ('promotion', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='arcsubs.Promotion', verbose_name='Promocion')),
            ],
            options={
                'verbose_name': 'Promocion del usuario',
                'verbose_name_plural': '[ARC] Promociones del usuario',
            },
        ),
    ]