# Generated by Django 2.2.9 on 2020-02-21 15:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0039_auto_20200220_1006'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arcuserreport',
            name='user',
            field=models.OneToOneField(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='arcsubs.ArcUser', verbose_name='Usuario'),
        ),
    ]
