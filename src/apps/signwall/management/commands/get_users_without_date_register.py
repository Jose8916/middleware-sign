from datetime import date, datetime, timedelta

import pytz
from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.arcsubs.models import ArcUser
from apps.signwall.models import MppUser


TIMEZONE = pytz.timezone('America/Lima')


class Command(BaseCommand):
    help = 'Actualiza first_login de usuarios migrados de ARC python manage.py load_first_logins 2019-07-03'

    def handle(self, *args, **options):
        list_user = []
        user_with_date = ArcUser.objects.filter(profile__createdOn__isnull=False)
        for user in user_with_date.iterator():
            list_user.append(user.uuid)

        lista_usuarios = ArcUser.objects.exclude(uuid__in=list_user)
        for usuario in lista_usuarios.iterator():
            try:
                print(usuario.uuid)
            except Exception:
                print(usuario.__dict__)

        print("> %s usuarios con fecha de creacion" % user_with_date.count())
