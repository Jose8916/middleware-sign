# Generated by Django 2.2.3 on 2019-12-23 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signwall', '0009_passarcuser'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MppUserStep',
        ),
        migrations.AlterField(
            model_name='passarcuser',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creado'),
        ),
        migrations.AlterField(
            model_name='passarcuser',
            name='last_updated',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modificado'),
        ),
    ]