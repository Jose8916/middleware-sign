# Generated by Django 3.0.1 on 2020-02-18 22:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0035_auto_20200218_1736'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='logarcuserreport',
            options={'ordering': ('created',), 'verbose_name': '[Log] Reporte Usuario de ARC', 'verbose_name_plural': '[Log] Reporte Usuarios'},
        ),
    ]
