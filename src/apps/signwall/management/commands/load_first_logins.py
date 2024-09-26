from datetime import date, datetime, timedelta

import pytz
from django.core.management.base import BaseCommand

from apps.arcsubs.models import ArcUser
from apps.signwall.models import MppUser


TIMEZONE = pytz.timezone('America/Lima')


class Command(BaseCommand):
    help = 'Actualiza first_login de usuarios migrados de ARC python manage.py load_first_logins 2019-07-03'

    def add_arguments(self, parser):
        parser.add_argument('date', nargs='?', type=str)

    def get_range(self, **options):

        if options.get('date'):
            day_str = options['date']
            raw_day = datetime.strptime(day_str, '%Y-%m-%d').date()
        else:
            raw_day = date.today() - timedelta(days=1)

        start_date = datetime.combine(
            raw_day,
            datetime.min.time()
        )
        end_date = datetime.combine(
            raw_day,
            datetime.max.time()
        )
        return (TIMEZONE.localize(start_date), TIMEZONE.localize(end_date))

    def handle(self, *args, **options):

        self.identify_mpp_users()

        _range = self.get_range(**options)

        # print(start_date, end_date)
        print("Rango: %s - %s" % _range)
        query_base = ArcUser.objects.filter(created_on__range=_range)

        # Usuarios sin first_login del día
        users = query_base.filter(first_login=None)
        print("> %s usuarios sin first_login" % users.count())
        for user in users:
            user.load_first_login(commit=False)
            if not user.first_login:
                user.update_arc_profile(commit=False)
                user.load_first_login(commit=False)
            user.save()

        # Usuarios con first_login sin first_login_method
        users = query_base.exclude(
            first_login=None
        ).filter(
            first_login_method=None
        )
        print("> %s usuarios con first_login sin first_login_method" % users.count())
        for user in users:
            user.update_arc_profile(commit=False)
            user.load_first_login(commit=False)
            user.save()

    def identify_mpp_users(self):
        # IDENTIFICA LOS USUARIOS MPP
        mpp_user_ids = []
        arc_user_ids = []
        users = ArcUser.objects.filter(
            from_mpp=None
        ).exclude(
            email__endswith='@facebook.com'
        )
        for user in users.iterator():
            from_mpp = False
            email = user.profile.get('email')

            if email:
                # Por email
                if MppUser.objects.filter(email=email.lower()).exists():
                    from_mpp = True

                # # Por Facebook ID

                if from_mpp:
                    mpp_user_ids.append(user.id)
                else:
                    arc_user_ids.append(user.id)

                if len(mpp_user_ids) > 200:
                    ArcUser.objects.filter(id__in=mpp_user_ids).update(from_mpp=True)
                    mpp_user_ids = []

                if len(arc_user_ids) > 200:
                    ArcUser.objects.filter(id__in=arc_user_ids).update(from_mpp=False)
                    arc_user_ids = []

        if mpp_user_ids:
            ArcUser.objects.filter(id__in=mpp_user_ids).update(from_mpp=True)

        if arc_user_ids:
            ArcUser.objects.filter(id__in=arc_user_ids).update(from_mpp=False)
