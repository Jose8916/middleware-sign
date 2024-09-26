# Generated by Django 3.0.1 on 2020-02-18 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0034_arcuserreport_logarcuserreport'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='logarcuserreport',
            options={'ordering': ('-created',), 'verbose_name': '[Log] Reporte Usuario de ARC', 'verbose_name_plural': '[Log] Reporte Usuarios'},
        ),
        migrations.AddField(
            model_name='logarcuserreport',
            name='site',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Site'),
        ),
    ]