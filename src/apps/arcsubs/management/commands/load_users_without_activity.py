# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings

from ...models import ArcUser
from os import path
import csv


class Command(BaseCommand):
    help = 'Ejecuta el comando'

    def add_arguments(self, parser):
        parser.add_argument('--cleanAll', nargs='?', type=str)

    def handle(self, *args, **options):
        if options.get('cleanAll'):
            ArcUser.objects.all().update(with_activity=None)
            print('se realizo la limpieza de with_activity')

        if settings.ENVIRONMENT == 'production':
            base_route = '/tmp/data.csv'
        else:
            base_route = "{}/data.csv".format(path.dirname(__file__))

        with open(base_route, 'r', encoding="ISO-8859-1") as file:
            csv_file = csv.DictReader(file)

            for row in csv_file:
                try:
                    if ArcUser.objects.filter(uuid=row.get('uuid')).exists():
                        ArcUser.objects.filter(uuid=row.get('uuid')).update(with_activity=True)
                except Exception as e:
                    print(e)
        return 'Ejecucion exitosa'