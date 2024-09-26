"""

"""

from os import path
import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from sentry_sdk import capture_exception

from ...models import ArcUser, Event
from apps.arcsubs.utils import timestamp_to_datetime
from apps.signwall.utils import search_user_arc_param


class Command(BaseCommand):
    help = 'Ejecuta el comando'

    def add_arguments(self, parser):
        parser.add_argument('--cleanAll', nargs='?', type=str)

    def handle(self, *args, **options):
        if options.get('cleanAll'):
            ArcUser.objects.all().update(date_verified=None)
            print('se realizo la limpieza de date_verified')

        count_event = 0
        events = Event.objects.filter(
            event_type='EMAIL_VERIFIED'
        )

        for event in events.iterator():
            uuid = event.message.get('uuid')
            last_updated_on = event.message.get('lastUpdatedOn')
            last_updated_on = timestamp_to_datetime(last_updated_on)
            arc_users = ArcUser.objects.filter(uuid=uuid, date_verified__isnull=True)
            if arc_users.exists():
                count_event = count_event + 1
                print(uuid)
                arc_users.update(date_verified=last_updated_on)

        print('--------------------')
        # Registra fecha de verificacion de email solo para los registros por facebook o Google
        count = 0
        users = ArcUser.objects.filter(
            date_verified__isnull=True,
            email_verified=True
        ).exclude(email__contains='facebook.com')

        for user in users.iterator():
            try:
                if user.identities:
                    list_identities = sorted(user.identities, key=lambda i: i['createdOn'])

                    for identity in list_identities[:1]:
                        if identity.get('type') in ['Facebook', 'Google']:
                            if user.profile.get('createdOn', ''):
                                user.date_verified = timestamp_to_datetime(user.profile['createdOn'])
                                print(user.uuid)
                                user.save()
                                count = count + 1
            except Exception as e:
                print(e)
                # capture_exception()

        print('Se actualizaron ' + str(count) + ' registros de redes sociales')
        print('Se actualizaron ' + str(count_event) + ' registros de Event verified email')
        return 'Ejecucion exitosa'
