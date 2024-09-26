from datetime import date, datetime, timedelta

import csv
import pytz
from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.arcsubs.models import ArcUser
from apps.signwall.models import MppUser
from apps.webutils.utils import validar_email
from sentry_sdk import capture_exception
from apps.arcsubs.arcclient import IdentityClient

TIMEZONE = pytz.timezone('America/Lima')


class Command(BaseCommand):
    help = 'valida si un usuario tiene suscripcion leyendo un csv de entrada'

    def handle(self, *args, **options):
        # name = '/tmp/lista_de_uid.csv'
        name = '/home/milei/Escritorio/lastlogin2.csv'
        list_dicts = []
        # with open('/tmp/users_with_subscription.csv', 'a') as csvFileWrite:
        with open('/home/milei/Escritorio/lista_2.csv', 'a') as csvFileWrite:
            writer = csv.writer(csvFileWrite)

            try:
                with open(name) as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        if IdentityClient().get_subscriptions_by_user('elcomercio', row[2]) or \
                                IdentityClient().get_subscriptions_by_user('gestion', row[2]):
                            writer.writerow(row)
                            print(row[2])
                        print(row[2])
            except Exception as e:
                print(e)
                capture_exception()
        print('fin')
        csvFileWrite.close()


