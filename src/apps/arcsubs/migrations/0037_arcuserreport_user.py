# Generated by Django 3.0.1 on 2020-02-18 23:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0036_auto_20200218_1738'),
    ]

    operations = [
        migrations.AddField(
            model_name='arcuserreport',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='arcsubs.ArcUser', verbose_name='Usuario'),
        ),
    ]