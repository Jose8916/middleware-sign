# Generated by Django 2.2.3 on 2019-08-29 01:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signwall', '0006_auto_20190828_1949'),
    ]

    operations = [
        # migrations.DeleteModel(
        #     name='ArcReport',
        # ),
        migrations.AddField(
            model_name='report',
            name='hits',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='Número de intentos'),
        ),
    ]
