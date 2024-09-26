# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q

from ...models import ArcUser, ArcUserExtraFields
from os import path
import csv


class Command(BaseCommand):
    help = 'Ejecuta el comando'
    # python manage.py load_data_treatment --update_data 1

    def add_arguments(self, parser):
        parser.add_argument('--report', nargs='?', type=str)
        parser.add_argument('--update_data', nargs='?', type=str)

    def handle(self, *args, **options):
        if options.get('update_data'):
            users_acr = ArcUser.objects.filter(profile__attributes__contains=[{'name': 'dataTreatment'}])

            for user_arc in users_acr.iterator():
                if not ArcUserExtraFields.objects.filter(arc_user=user_arc).exists():
                    list_attributes = user_arc.profile.get('attributes', []) or []

                    for attrib in list_attributes:
                        if attrib.get('name', '') == 'dataTreatment':
                            value_data_treat = attrib.get('value', '')
                            arcuser_extra = ArcUserExtraFields(arc_user=user_arc, data_treatment=value_data_treat)
                            arcuser_extra.save()
        print('Ejecucion exitosa')

