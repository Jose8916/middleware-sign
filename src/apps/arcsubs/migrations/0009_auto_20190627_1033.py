# Generated by Django 2.2 on 2019-06-27 15:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0008_auto_20190627_1032'),
    ]

    operations = [
        migrations.RenameField(
            model_name='arcuser',
            old_name='identities',
            new_name='first_identities',
        ),
    ]
