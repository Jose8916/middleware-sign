# Generated by Django 2.2 on 2019-05-29 03:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='arcuser',
            name='username',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='username'),
        ),
    ]
