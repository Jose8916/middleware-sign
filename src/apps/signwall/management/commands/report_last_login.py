import pytz
import time
import csv
from django.conf import settings
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from django.utils import formats, timezone
from apps.arcsubs.models import ArcUser, DeletedUser
from django.utils.encoding import smart_str


class Command(BaseCommand):
    help = 'Actualiza data de usuarios migrados de MPP a ARC Publishing'

    def add_arguments(self, parser):
        parser.add_argument('--dias', nargs='?', type=str)

    def handle(self, *args, **options):
        ahora = datetime.utcnow()
        last_month = ahora - timedelta(days=int(options.get('dias')))
        users = ArcUser.objects.exclude(last_login__range=[last_month, ahora])
        with open('/tmp/reporte_last_login_13_set.csv', 'a') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow([
                smart_str(u"UUID"),
                smart_str(u"Ultimo Login")
            ])
            for user in users.iterator():
                try:
                    tz = timezone.get_current_timezone()
                    last_login = formats.date_format(user.last_login.astimezone(tz), settings.DATETIME_FORMAT)
                except Exception as e:
                    last_login = e
                row = [
                    user.uuid,
                    last_login
                ]
                writer.writerow(row)
        csvFile.close()
