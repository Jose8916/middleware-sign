# Generated by Django 2.2 on 2019-07-03 16:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0015_auto_20190703_1055'),
    ]

    operations = [
        migrations.RenameField(
            model_name='arcuser',
            old_name='first_identities',
            new_name='first_login_identities',
        ),
    ]
