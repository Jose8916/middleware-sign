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
        query_base = ArcUser.objects.filter(Q(profile='') | Q(profile=None) | Q(profile='null') |
                                            Q(profile__createdOn='') | Q(profile__createdOn=None) |
                                            Q(profile__createdOn='null') | Q(profile__createdOn__isnull=True))
        print("> %s usuarios sin fecha de creacion" % query_base.count())

        for instance in query_base.iterator():
            print(instance.uuid)
            instance.update_arc_profile(commit=False)
            instance.load_first_login(commit=False)
            instance.save()

        user_with_date = ArcUser.objects.filter(profile__createdOn__isnull=False)
        print("> %s usuarios con fecha de creacion" % user_with_date.count())
