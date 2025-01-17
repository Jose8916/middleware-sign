# Generated by Django 2.2 on 2019-06-05 22:53

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arcsubs', '0002_arcuser_username'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ArcEvent',
        ),
        migrations.RemoveField(
            model_name='sendmail',
            name='mail_template',
        ),
        migrations.RemoveField(
            model_name='arcuser',
            name='identity',
        ),
        migrations.AddField(
            model_name='arcuser',
            name='identities',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='identities'),
        ),
        migrations.DeleteModel(
            name='Logs',
        ),
        migrations.DeleteModel(
            name='MailTemplate',
        ),
        migrations.DeleteModel(
            name='SendMail',
        ),
    ]
