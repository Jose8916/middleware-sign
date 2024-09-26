from datetime import datetime, timedelta
from urllib.parse import urljoin
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone
from sentry_sdk import capture_message, capture_event
import requests

from apps.arcsubs.models import ArcUser, ArcUserReport, LogArcUserReport
from apps.signwall.models import UsersReport
from apps.signwall.utils import utc_to_local_time_zone, search_user_arc_param


class Command(BaseCommand):
    help = 'Almacena los reportes de ARC en la tabla ArcUserReport'
    # fecha de inicio: 2019-07-09(año - mes - dia)
    # fecha de fin: 2019-07-10(año - mes - dia)
    # python3 manage.py load_report_arc  --startDate "2019-06-05" --endDate "2019-06-06" --site "elcomercio"  #por rango de fechas
    # python3 manage.py load_report_arc  --hoursAgo 3 --site "elcomercio"  #hace 3 horas
    # python3 manage.py load_users_from_arc_report --daysAgo 1 --site "elcomercio"  #hace un dia

    def mkDateTime(self, dateString, strFormat="%Y-%m-%d"):
        # Expects "YYYY-MM-DD" string
        # returns a datetime object

        eSeconds = time.mktime(time.strptime(dateString, strFormat))
        return datetime.fromtimestamp(eSeconds)

    def formatDate(self, dtDateTime, strFormat="%Y-%m-%d"):
        # format a datetime object as YYYY-MM-DD string and return
        return dtDateTime.strftime(strFormat)

    def mkFirstOfMonth2(self, dtDateTime):
        # what is the first day of the current month
        ddays = int(dtDateTime.strftime("%d")) - 1  # days to subtract to get to the 1st
        delta = timedelta(days=ddays)  # create a delta datetime object
        d = dtDateTime - delta  # Subtract delta and return
        return d.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

    def mkFirstOfMonth(self, dtDateTime):
        # what is the first day of the current month
        # format the year and month + 01 for the current datetime, then form it back
        # into a datetime object
        return mkDateTime(formatDate(dtDateTime, "%Y-%m-01"))

    def mkLastOfMonth(self, dtDateTime):
        # return datetime.date(d.year, d.month + 1, d.day) - datetime.timedelta(1)

        dYear = dtDateTime.strftime("%Y")  # get the year
        dMonth = str(int(dtDateTime.strftime("%m")) % 12 + 1)  # get next month, watch rollover
        dDay = "1"  # first day of next month
        nextMonth = self.mkDateTime("%s-%s-%s" % (dYear, dMonth, dDay))  # make a datetime obj for 1st of next month
        delta = timedelta(seconds=1)  # create a delta of 1 second
        r = nextMonth - delta  # subtract from nextMonth and return
        return r.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

    def report_post(self, startDate, endDate, site):
        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + settings.PAYWALL_ARC_TOKEN,
            'Arc-Site': '' + str(site)
        }

        payload = {
            "name": "reporte_arc",
            "startDate": startDate,
            "endDate": endDate,
            "reportType": "sign-up-summary",
            "reportFormat": "json"
        }

        url = urljoin(settings.PAYWALL_ARC_URL, 'identity/api/v1/report/schedule')
        try:
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            log_arc_user_report = LogArcUserReport(
                schedule_request=payload,
                schedule_response=result,
                site=str(site))
            return result, log_arc_user_report
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

    def report_post_days(self, daysAgo, site):
        start_day = datetime.combine(
            datetime.now() - timedelta(days=int(daysAgo)),
            datetime.min.time()
        )
        end_day = datetime.combine(
            datetime.now(),
            datetime.min.time()
        )

        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + settings.PAYWALL_ARC_TOKEN,
            'Arc-Site': '' + str(site)
        }

        payload = {
            "name": "reporte_arc",
            "startDate": start_day.strftime('%Y-%m-%dT%H:%M:%S') + ".000Z",
            "endDate": end_day.strftime('%Y-%m-%dT%H:%M:%S') + ".000Z",
            "reportType": "sign-up-summary",
            "reportFormat": "json"
        }
        url = urljoin(settings.PAYWALL_ARC_URL, 'identity/api/v1/report/schedule')
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == requests.codes.ok:
                return response.json()
            else:
                print(response.text)
                capture_event(
                    {
                        'message': 'Fallo en Metodo Post report schedule',
                        'extra': {
                            'payload': payload,
                            'url': settings.PAYWALL_ARC_URL + 'identity/api/v1/report/schedule',
                            'response': response.text
                        }
                    }
                )
                return ""
        except Exception:
            capture_event(
                {
                    'message': 'Fallo en Metodo Post report schedule',
                    'extra': {
                        'payload': payload,
                        'url': settings.PAYWALL_ARC_URL + 'identity/api/v1/report/schedule'
                    }
                }
            )
            print('Error en en API Post de reportes de ARC')
            return ""

    def report_post_days_all(self, daysAgo, site):
        start_day = int(daysAgo) + 5
        start_day = datetime.combine(
            datetime.now() - timedelta(days=start_day),
            datetime.min.time()
        )

        end_day = datetime.combine(
            datetime.now() - timedelta(days=int(daysAgo)),
            datetime.min.time()
        )

        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + settings.PAYWALL_ARC_TOKEN,
            'Arc-Site': '' + str(site)
        }

        payload = {
            "name": "reporte_arc",
            "startDate": start_day.strftime('%Y-%m-%dT%H:%M:%S') + ".000Z",
            "endDate": end_day.strftime('%Y-%m-%dT%H:%M:%S') + ".000Z",
            "reportType": "sign-up-summary",
            "reportFormat": "json"
        }
        print('------------------------------')
        print(site)
        print(payload)
        print('------------------------------')
        url = urljoin(settings.PAYWALL_ARC_URL, 'identity/api/v1/report/schedule')
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == requests.codes.ok:
                return response.json()
            else:
                print(response.text)
                capture_event(
                    {
                        'message': 'Fallo en Metodo Post report schedule',
                        'extra': {
                            'payload': payload,
                            'url': settings.PAYWALL_ARC_URL + 'identity/api/v1/report/schedule',
                            'response': response.text
                        }
                    }
                )
                return ""
        except Exception:
            capture_event(
                {
                    'message': 'Fallo en Metodo Post report schedule',
                    'extra': {
                        'payload': payload,
                        'url': settings.PAYWALL_ARC_URL + 'identity/api/v1/report/schedule'
                    }
                }
            )
            print('Error en en API Post de reportes de ARC')
            return ""

    def get_last_modified_date(self, obj):
        try:
            return utc_to_local_time_zone(obj.get('lastModifiedDate', ''))
        except Exception:
            return ''

    def get_last_login_date(self, obj):
        try:
            return utc_to_local_time_zone(obj.get('lastLoginDate', ''))
        except Exception:
            return ''

    def get_create_on(self, obj):
        try:
            return utc_to_local_time_zone(obj.get('createdOn', ''))
        except Exception:
            return ''

    def get_arc_user(self, uuid):
        try:
            return ArcUser.objects.get(uuid=uuid)
        except Exception:
            return None

    def load_user(self, user_data, site):
        result = user_data.get('result', '')[0]
        user_data = result.get('profile', '')
        uuid = result.get('uuid', '')

        headers = {
            'content-type': 'application/json'
        }

        payload = {
            "eventTime": user_data['createdOn'],
            "index": user_data['createdOn'],
            "message":
                {
                    "email": user_data['email'],
                    "identifier": user_data['email'],
                    "uuid": uuid
                },
            "site": str(site),
            "type": 'USER_SIGN_UP'
        }

        url = settings.EVENTS_LAMBDA + str('/v1/service/arc/events')

        try:
            print('evento enviado: ' + str(uuid))
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()

            return result
        except Exception:
            capture_event(
                {
                    'message': 'Error al enviar evento de registro',
                    'extra': {
                        'url': url,
                        'payload': payload,
                        'header': headers
                    }
                }
            )
            print('Error al enviar evento de registro')
            return ""

    def report_download(self, jobid, site, body_from_post):
        url = settings.PAYWALL_ARC_URL + "identity/api/v1/report/" + str(jobid) + "/download"

        payload = ""
        headers = {
            'Content-Type': "application/json",
            'Authorization': "Bearer " + settings.PAYWALL_ARC_TOKEN,
            'cache-control': "no-cache",
            'Arc-Site': '' + str(site)
        }
        try:
            response = requests.request("GET", url, data=payload, headers=headers)
            print(response)
            if response.status_code == 200:
                if len(response.json()) > 1:
                    for obj in response.json():
                        if not ArcUserReport.objects.filter(uuid=obj.get('clientId', '')).exists():
                            arc_user = self.get_arc_user(obj.get('clientId', ''))
                            if arc_user:
                                user = ArcUserReport(
                                    uuid=obj.get('clientId', ''),
                                    last_modified_date=self.get_last_modified_date(obj),
                                    last_login_date=self.get_last_login_date(obj),
                                    created_on=self.get_create_on(obj),
                                    site=str(site),
                                    body=obj,
                                    user=arc_user
                                )
                                user.save()
                            else:
                                user = ArcUserReport(
                                    uuid=obj.get('clientId', ''),
                                    last_modified_date=self.get_last_modified_date(obj),
                                    last_login_date=self.get_last_login_date(obj),
                                    created_on=self.get_create_on(obj),
                                    site=str(site),
                                    body=obj,
                                    user=None
                                )
                                user.save()
                                # envia eventos se guardara al dia siguiente
                                user_data = search_user_arc_param('uuid', obj.get('clientId', ''))
                                if user_data.get('totalCount', ''):
                                    respuesta = self.load_user(user_data, site)

                # log_arc_user_report.download_total = len(response.json())
                # log_arc_user_report.save()
            else:
                capture_event(
                    {
                        'message': 'Fallo en la peticion de datos del reporte GET',
                        'extra': {
                            'url': url,
                            'response': response,
                            'body_from_post': body_from_post
                        }
                    }
                )
        except Exception as e:
            capture_event(
                {
                    'message': 'Fallo en la descarga de datos del reporte',
                    'extra': {
                        'url': url,
                        'error': e,
                        'body_from_post': body_from_post
                    }
                }
            )

    def add_arguments(self, parser):
        parser.add_argument('--startDate', nargs='?', type=str)
        parser.add_argument('--year', nargs='?', type=str)
        parser.add_argument('--endDate', nargs='?', type=str)
        parser.add_argument('--hoursAgo', nargs='?', type=str)
        parser.add_argument('--site', nargs='?', type=str)
        parser.add_argument('--daysAgo', nargs='?', type=str)
        parser.add_argument('--all', nargs='?', type=str)

    def format_date(self, createdOn):
        createdOn_format = datetime.strptime(createdOn, "%Y-%m-%d %H:%M:%S")
        return get_default_timezone().localize(createdOn_format)

    def handle(self, *args, **options):
        if options.get('year') and options.get('site'):
            if options.get('year') == '2019':
                range_month = 12
            else:
                range_month = 2

            for i in range(range_month):
                thisMonth = ("0%i" % (i + 1,))[-2:]
                fecha_query = '{year}-{month}-02'.format(year=options.get('year'), month=thisMonth)

                d = self.mkDateTime(fecha_query)
                first_step_report, log_arc_user_report = \
                    self.report_post(self.mkFirstOfMonth2(d) + 'Z', self.mkLastOfMonth(d) + 'Z', options.get('site'))

                if first_step_report:
                    jobid = first_step_report.get('jobID', '')
                    time.sleep(40)
                    self.report_download(jobid, options.get('site'), log_arc_user_report)
                    time.sleep(10)
                print('Ejecucion exitosa')

        if options.get('startDate') and options.get('endDate') and options.get('site'):
            first_step_report, log_arc_user_report = \
                self.report_post(options.get('startDate'), options.get('endDate'), options.get('site'))

            if first_step_report:
                jobid = first_step_report.get('jobID', '')
                time.sleep(40)
                self.report_download(jobid, options.get('site'), log_arc_user_report)
            print('Ejecucion exitosa')

        if options.get('all'):
            list_site = ['depor', 'diariocorreo', 'elbocon', 'elcomercio', 'gestion', 'peru21', 'trome']
            for site in list_site:
                # for nro in range(15, 0, -5):
                for nro in range(527, 0, -5):
                    first_step_report = self.report_post_days_all(nro, site)
                    if first_step_report:
                        jobid = first_step_report.get('jobID', '')
                        time.sleep(20)
                        self.report_download(jobid, site, first_step_report)
                        time.sleep(10)
                    print('Ejecucion exitosa')

        if options.get('hoursAgo'):
            first_step_report = self.report_post_last_hours(options.get('hoursAgo'), options.get('site'))
            if first_step_report:
                jobid = first_step_report.get('jobID', '')
                time.sleep(10)
                self.report_download(jobid, options.get('site'))
            print('Ejecucion exitosa')
        if options.get('daysAgo'):
            list_site = ['depor', 'diariocorreo', 'elbocon', 'elcomercio', 'gestion', 'peru21', 'trome']
            for site in list_site:
                first_step_report = self.report_post_days(options.get('daysAgo'), site)
                if first_step_report:
                    jobid = first_step_report.get('jobID', '')
                    time.sleep(10)
                    self.report_download(jobid, site)
                else:
                    print('Fallo en la peticion POST del reporte')
        else:
            print('Use: python manage.py load_report_arc  --startDate "2019-08-01" --endDate "2019-08-20" --site "elcomercio"')
