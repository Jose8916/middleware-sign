# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from ...models import ArcUser
from django.conf import settings
from os import path

import csv
import requests


class Command(BaseCommand):
    help = 'Ejecuta el comando'
    API_ENDPOINT = settings.DOMAIN_PAYWALL_MIDDLEWARE + '/api/user_with_subscription/'

    def add_arguments(self, parser):
        parser.add_argument('--loadCsv', nargs='?', type=str)
        parser.add_argument('--loadByAPI', nargs='?', type=str)
        parser.add_argument('--cleanData', nargs='?', type=str)

    def handle(self, *args, **options):
        if options.get('cleanData'):
            ArcUser.objects.all().update(with_subscription=None)
            arc_user_total = ArcUser.objects.filter(with_subscription=True).count()
            print('Hay ' + str(arc_user_total) + " usuarios con suscripcion")
        if options.get('loadCsv'):
            """
            if settings.ENVIRONMENT == 'production':
                base_route = '/tmp/subscriptions.csv'
            else:
                base_route = "{}/subscriptions.csv".format(path.dirname(__file__))
            """
            base_route = "{}/subscriptions.csv".format(path.dirname(__file__))
            i = 0

            with open(base_route, 'r', encoding='utf-8') as file:
                csv_file = csv.DictReader(file)
                count_csv = 0
                for row in csv_file:
                    count_csv = count_csv + 1

                    try:
                        arc_user = ArcUser.objects.filter(uuid=row.get('uuid')).exclude(with_subscription=True)
                        if arc_user.exists():
                            arc_user.update(with_subscription=True)
                            i = i + 1
                    except Exception as e:
                        print(e)
                        continue

            print('Se ejecutaron ' + str(i) + 'registros')
            print('El csv contenia ' + str(count_csv) + ' registros')

        if options.get('loadByAPI'):
            users = ArcUser.objects.filter(
                email__contains='mailinator.com'
            ).exclude(with_subscription=True)
            headers = {
                'content-type': 'application/json',
                'Authorization': 'Token ' + settings.TOKEN_PAYWALL_MIDDLEWARE
            }

            for user in users.iterator():
                payload = {'uuid': user.uuid}
                response = requests.post(url=self.API_ENDPOINT, json=payload, headers=headers)
                data_user = response.json()

                try:
                    if data_user.get('value'):
                        ArcUser.objects.filter(uuid=user.uuid).update(with_subscription=True)
                except Exception as e:
                    print(e)
                    continue
            return 'Ejecucion exitosa'