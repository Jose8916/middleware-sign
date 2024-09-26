# Generated by Django 2.2.9 on 2020-06-25 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0041_arcuserdeletedproxymodel'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ArcUserDeletedProxyModel',
        ),
        migrations.AddField(
            model_name='arcuser',
            name='without_activity',
            field=models.NullBooleanField(default=False, verbose_name='Sin actividad'),
        ),
    ]
