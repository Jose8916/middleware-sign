# Generated by Django 2.2.9 on 2020-11-06 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0054_arcuser_date_verified'),
    ]

    operations = [
        migrations.AddField(
            model_name='arcuser',
            name='display_name',
            field=models.CharField(blank=True, db_index=True, max_length=150, null=True, verbose_name='Display Name'),
        ),
    ]
