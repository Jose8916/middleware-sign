from datetime import date, datetime, timedelta

import pytz
from django.core.management.base import BaseCommand

from apps.arcsubs.models import ArcUser
from apps.signwall.models import MppUser


TIMEZONE = pytz.timezone('America/Lima')


class Command(BaseCommand):
    help = 'Actualiza el last login de usuarios'

    def handle(self, *args, **options):
        users = ArcUser.objects.all()
        for user in users.iterator():
            lista_last_login = []
            if user.identities:
                if len(user.identities):
                    for identity in user.identities:
                        if identity.get('lastLoginDate', ''):
                            lista_last_login.append(int(identity.get('lastLoginDate', '')))

                    if lista_last_login:
                        last_login_uTimestamp = max(lista_last_login)
                        user.last_login = datetime.fromtimestamp(last_login_uTimestamp / 1000.0)
                        user.save()
