# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.conf import settings

from ...models import ArcUser
from os import path
from apps.signwall.utils import search_user_arc_param
import csv
import pytz
from datetime import datetime, timedelta

TIMEZONE = pytz.timezone('America/Lima')


class Command(BaseCommand):
    help = 'Ejecuta el comando'

    def add_arguments(self, parser):
        parser.add_argument('--cleanAll', nargs='?', type=str)

    def handle(self, *args, **options):
        start_date = datetime.now(TIMEZONE) - timedelta(days=10)

        if options.get('cleanAll'):
            ArcUser.objects.all().update(email_verified=None)
            print('se realizo la limpieza de with_activity')
        """
        users = ArcUser.objects.filter(
            created_on__range=[start_date, datetime.now(TIMEZONE)]
        ).exclude(
            email_verified=True
        )
        """
        users = ArcUser.objects.exclude(email_verified=True)
        count = 0
        for user in users.iterator():
            if user.profile.get('emailVerified') is True:
                print(user.uuid)
                user.email_verified = True
                user.save()
                count = count + 1
            """    
            user_data = search_user_arc_param('uuid', user.uuid)
            try:
                if user_data:
                    if user_data.get('totalCount', ''):
                        result = user_data.get('result', '')[0]
                        user_data = result.get('profile', '')
                        uuid = result.get('uuid', '')

                        if user_data['emailVerified'] is True:
                            count = count + 1
                            ArcUser.objects.filter(uuid=uuid).update(email_verified=True)
            except Exception as e:
                print(e)
            """

        print(str(count) + ' registros actualizados')

        return 'Ejecucion exitosa'