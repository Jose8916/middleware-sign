from pydoc import cli
from datetime import date, datetime, timedelta
import time
import csv

from django.core.management.base import BaseCommand

from apps.arcsubs.arcclient import ArcClientAPI

def dates_format(date_init, date_end):
    # date_init = '2022-01-30T00:00:00Z'
    # date_end = '2018-01-30T00:00:00Z'

    di = datetime.strptime(date_init, "%Y-%m-%dT%H:%M:%SZ")
    de = datetime.strptime(date_end, "%Y-%m-%dT%H:%M:%SZ")
    
    return di, de


class Command(BaseCommand):
    help = ("Exporta uuid de usuarios para migración a piano", )
    
    def add_arguments(self, parser):

        # To run for one ser with uuid
        parser.add_argument("--date_major", type=str, help=("Fecha más reciente"))
        parser.add_argument('--date_minor', type=str, help=("Fecha más antigua"))

    def handle(self, *args, **options):
        client = ArcClientAPI()
        
        di, de = dates_format(options["date_major"], options['date_minor'])
        total_weeks = (di-de).days//7
        backe = di
        reports_ids = list()
        for _ in range(total_weeks):
            backi = backe
            backe = backi - timedelta(days=7)
            report_id = client.create_report(f"{backe.date()}T{backe.time()}.000Z", f"{backi.date()}T{backi.time()}.000Z", "account-activity-last-modified", 'elcomercio')
            reports_ids.append(report_id)
        time.sleep(3000)
        for report_id in reports_ids:
            with open('/home/milei/Escritorio/last_login.csv', 'a') as csvFileWrite:
                writer = csv.writer(csvFileWrite)
                response = client.download_report(report_id)
                for obj in response:
                    writer.writerow(
                        [
                            obj.get('emailVerified'),
                            obj.get('modifiedOn'),
                            obj.get('clientId'),
                            obj.get('identityType'),
                            obj.get('lastLoginDate'),
                            obj.get('createdOn'),
                            obj.get('status')
                        ])
            csvFileWrite.close()
