from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand
import pytz

from apps.arcsubs.models import ArcUser
from apps.signwall.models import ArcReport


class Command(BaseCommand):
    help = 'Carga los usuarios usando el API de reportes de ARC python manage.py load_first_login 2019-07-03'

    def add_arguments(self, parser):
        parser.add_argument('date', nargs='?', type=str)

    def handle(self, *args, **options):
        tz = pytz.timezone('America/Lima')
        if options.get('date'):
            day_str = options['date']
            day_raw = datetime.strptime(day_str, '%Y-%m-%d').date()
        else:
            day_raw = date.today() - timedelta(days=1)

        start_date = datetime.combine(
            day_raw,
            datetime.min.time()
        )
        end_date = datetime.combine(
            day_raw,
            datetime.max.time()
        )
        report_type = ArcReport.REPORT_TYPE_SIGN_UP

        try:
            ArcReport.objects.get(start_date=start_date, end_date=end_date, report_type=report_type)
        except Exception as e:
            raise e

        print(start_date, end_date)
        print(tz.localize(start_date), tz.localize(end_date))
        query_base = ArcUser.objects.filter(created_on__range=(tz.localize(start_date), tz.localize(end_date)))
        print(query_base.count())
        # Usuarios de MPP (Sólo día anterior)
        query_base.filter(from_mpp=True)

        # Usuarios nuevos (Sólo día anterior)
        query_base.exclude(from_mpp=True)

        # Usuarios con first_login sin first_login_identities

        # Usuarios con first_login sin method

        # Usuarios de ARC con first_login sin method

        # Usuarios de ARC con first_login sin method
