from datetime import datetime

import pytz
from django.core.management.base import BaseCommand

from apps.arcsubs.models import ArcUser
# from apps.signwall.models import MppUserStep


TIMEZONE = pytz.timezone('America/Lima')


class Command(BaseCommand):
    help = 'Actualiza data de usuarios migrados de MPP a ARC Publishing'

    def handle(self, *args, **options):
        # SE ACTUALIZA first_login DE NUEVOS USUARIOS ARC
        users = ArcUser.objects.filter(first_login=None)
        print("> %s usuarios sin first_login" % users.count())
        for user in users.iterator():
            user.update_arc_profile(commit=False)
            user.load_first_login(commit=False)
            user.save()

        # SE ACTUALIZA fist_login DE USUARIOS SIN first_login_method
        users = ArcUser.objects.exclude(first_login=None).filter(first_login_method=None)
        print("> %s usuarios con first_login sin first_login_method" % users.count())
        for user in users.iterator():
            user.update_arc_profile(commit=False)
            user.load_first_login(commit=False)
            user.save()

    def load_first_login(self):
        # SE ACTUALIZA first_login DE NUEVOS USUARIOS ARC
        users = ArcUser.objects.exclude(from_mpp=True).filter(first_login=None)
        print("> %s usuarios ARC sin first_login" % users.count())
        for user in users.iterator():
            user.update_arc_profile(commit=False)
            user.load_first_login(commit=False)
            user.save()

        # SE ACTUALIZA fist_login DE USUARIOS SIN first_login_method
        users = ArcUser.objects.exclude(first_login=None).filter(first_login_method=None)
        print("> %s usuarios con first_login sin first_login_method" % users.count())
        for user in users.iterator():
            user.update_arc_profile(commit=False)
            user.load_first_login(commit=False)
            user.save()

        # SE ACTUALIZA first_login DE NUEVOS USUARIOS ARC
        users = ArcUser.objects.filter(profile__contains={"code": "3001001"})
        print("> %s usuarios sin profile" % users.count())
        for user in users.iterator():
            user.update_arc_profile(commit=False)
            user.load_first_login(commit=False)
            user.save()
        users = ArcUser.objects.filter(profile__contains={"code": "3001001"})
        print("> %s usuarios sin profile" % users.count())

        # CARGA EL PRIMER LOGIN
        users = ArcUser.objects.filter(first_login=None).exclude(created_on=None).iterator()
        for user in users:
            user.load_first_login(commit=False)

            if not user.first_login and user.from_mpp:
                if user.event_type == 'PASSWORD_RESET' or user.event_type == 'PROFILE_EDIT':
                    timestamp = user.profile.get('modifiedOn')
                    user.first_login = self.get_datetime_from_timestamp(timestamp)

            if not user.first_login and not user.from_mpp:
                timestamp = user.profile.get('createdOn')
                user.first_login = self.get_datetime_from_timestamp(timestamp)

            # PARA ACTUALIZAR FIRST_LOGIN DE FECHAS PASADAS
            step_migration = None
            step_password = None
            step = None
            steps = []
            email = user.profile.get('email')
            limit = TIMEZONE.localize(datetime(year=2019, month=7, day=4))
            if email and user.from_mpp and user.created_on < limit:
                steps = MppUserStep.objects.filter(us_email=email)
                for step_obj in steps:
                    if step_obj.type == 'MIGRATED_USER':
                        step_migration = step_obj

                    if step_obj.type == 'ASSIGNED_PASSWORD':
                        step_password = step_obj

                if step_migration and step_password:
                    if step_migration.date_register > step_password.date_register:
                        step = step_migration
                    else:
                        step = step_password

                elif step_migration:
                    step = step_migration

                elif step_password:
                    step = step_password

                if step and (user.first_login is None or (user.first_login and step.date_register < user.first_login)):
                    user.first_login = step.date_register
                    user.first_login_method = 'Password'

            user.save()

        # LIMPIA LOS first_login_identities SIN LOGIN
        users = ArcUser.objects.filter(identities=None)
        for user in users:
            user.identities = user.first_login_identities
            user.first_login_identities = None
            user.save()
        ArcUser.objects.filter(first_login_identities__contains=[{'lastLoginDate': None}]).update(first_login_identities=None)

    def get_datetime_from_timestamp(self, timestamp):
        return datetime.fromtimestamp(
            timestamp / 1000,
            tz=TIMEZONE
        )
