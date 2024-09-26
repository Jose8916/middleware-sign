from datetime import datetime, timedelta
from urllib.parse import urljoin
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone
from sentry_sdk import capture_message
import requests

from apps.arcsubs.models import ArcUser
from apps.signwall.models import UsersReport


class Command(BaseCommand):
    help = 'Comando que permite actualizar el created_on'
    # fecha de inicio: 2019-07-09(año - mes - dia)
    # fecha de fin: 2019-07-10(año - mes - dia)
    # python3 manage.py load_report_arc  --startDate "2019-06-05" --endDate "2019-06-06" --site "elcomercio"  #por rango de fechas
    # python3 manage.py load_report_arc  --hoursAgo 3 --site "elcomercio"  #hace 3 horas

    def report_post(self, startDate, endDate, site):
        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + settings.PAYWALL_ARC_TOKEN,
            'Arc-Site': '' + str(site)
        }

        payload = {
            "name": "reporte_arc",
            "startDate": startDate + "T05:00:00.000Z",
            "endDate": endDate + "T05:00:00.000Z",
            "reportType": "sign-up-summary",
            "reportFormat": "json"
        }

        url = urljoin(settings.PAYWALL_ARC_URL, 'identity/api/v1/report/schedule')
        try:
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            return result
        except Exception:
            print('Error en en API de reportes de ARC')
            return ""

    def report_post_last_hours(self, hoursAgo, site):
        # datetime.datetime.now()
        print(datetime.utcnow())
        startDate = datetime.utcnow() - timedelta(hours=int(hoursAgo))
        startDate_point = str(startDate).split('.')
        startDate_list = startDate_point[0].split(' ')

        endDate = datetime.utcnow()
        endDate_point = str(endDate).split('.')
        endDate_list = endDate_point[0].split(' ')

        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + settings.PAYWALL_ARC_TOKEN,
            'Arc-Site': '' + str(site)
        }

        payload = {
            "name": "reporte_arc",
            "startDate": startDate_list[0] + "T" + startDate_list[1] + ".000Z",
            "endDate": endDate_list[0] + "T" + endDate_list[1] + ".000Z",
            "reportType": "sign-up-summary",
            "reportFormat": "json"
        }
        url = urljoin(settings.PAYWALL_ARC_URL, 'identity/api/v1/report/schedule')
        try:
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            return result
        except Exception:
            print('Error en en API de reportes de ARC')
            return ""

    def report_download(self, jobid, site):
        url = settings.PAYWALL_ARC_URL + "identity/api/v1/report/" + str(jobid) + "/download"

        payload = ""
        headers = {
            'Content-Type': "application/json",
            'Authorization': "Bearer " + settings.PAYWALL_ARC_TOKEN,
            'cache-control': "no-cache",
            'Arc-Site': '' + str(site)
        }

        response = requests.request("GET", url, data=payload, headers=headers)

        if response.status_code == 200:
            if UsersReport.objects.all().count():
                UsersReport.objects.all().delete()

            for obj in response.json():
                user = UsersReport(user_profile=obj)
                user.save()
        else:
            capture_message('sobrepaso el tiempo')

    def add_arguments(self, parser):
        parser.add_argument('--startDate', nargs='?', type=str)
        parser.add_argument('--endDate', nargs='?', type=str)
        parser.add_argument('--hoursAgo', nargs='?', type=str)
        parser.add_argument('--site', nargs='?', type=str)

    def format_date(self, createdOn):
        createdOn_format = datetime.strptime(createdOn, "%Y-%m-%d %H:%M:%S")
        return get_default_timezone().localize(createdOn_format)

    def handle(self, *args, **options):
        if options.get('startDate') and options.get('endDate') and options.get('site'):
            first_step_report = self.report_post(options.get('startDate'), options.get('endDate'), options.get('site'))
            if first_step_report:
                jobid = first_step_report.get('jobID', '')
                time.sleep(40)
                self.report_download(jobid, options.get('site'))
            print('Ejecucion exitosa')

        elif options.get('hoursAgo'):
            first_step_report = self.report_post_last_hours(options.get('hoursAgo'), options.get('site'))
            if first_step_report:
                jobid = first_step_report.get('jobID', '')
                time.sleep(25)
                self.report_download(jobid, options.get('site'))

                user_reports = UsersReport.objects.all()
                for user_report in user_reports:
                    uuid = user_report.user_profile.get('clientId', '')
                    created_on = self.format_date(user_report.user_profile.get('createdOn', ''))
                    if uuid and created_on:
                        ArcUser.objects.filter(
                            uuid=uuid
                        ).exclude(created_on__isnull=False).update(created_on=created_on)

                        user_report.state = False
                        user_report.save()
            print('Ejecucion exitosa')
        else:
            print('Use: python manage.py load_report_arc  --startDate "2019-08-01" --endDate "2019-08-20" --site "elcomercio"')
