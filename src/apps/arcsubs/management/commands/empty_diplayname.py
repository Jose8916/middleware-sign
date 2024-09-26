# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q

from ...models import ArcUser
from os import path
import csv


class Command(BaseCommand):
    help = 'Ejecuta el comando'

    def add_arguments(self, parser):
        parser.add_argument('--report', nargs='?', type=str)
        parser.add_argument('--update_display', nargs='?', type=str)

    def handle(self, *args, **options):
        if options.get('report'):
            users = ArcUser.objects.all()
            for user in users.iterator():
                if user.profile.get('displayName', '') == '' or user.profile.get('displayName', '') is None \
                        or '@' not in user.profile.get('displayName', ''):
                    print(str(user.uuid) + ' - ' + str(user.profile.get('displayName', '')) + ' - ' + str(user.email))

            return 'Ejecucion exitosa'

        if options.get('update_display'):
            users_acr = ArcUser.objects.filter(Q(display_name="") | Q(display_name__isnull=True))
            print(users_acr.query)

            for user_arc in users_acr.iterator():
                if user_arc.profile.get('displayName', ''):
                    user_arc.display_name = user_arc.profile.get('displayName', '')
                    user_arc.save()

            return 'Ejecucion exitosa'

