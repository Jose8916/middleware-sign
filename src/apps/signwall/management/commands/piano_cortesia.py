import csv
import json
import os
import threading
from datetime import datetime
import pandas as pd

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone

from apps.arcsubs.arcclient import ArcClientAPI
from .migration_to_piano.piano_clients import PianoClient
from .migration_to_piano.utils import \
    format_name_date, period_dates_for_report, form_date_ranges, join_files


class Command(BaseCommand):
    help = ("Exporta subs Free Linked", )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = f"{settings.BASE_DIR}/reports_migration"
        self.name_file = format_name_date()
        self.path_subs = f"{self.path}/subs-{self.name_file}"
        self.path_subs_details = str()
        self.client = ArcClientAPI()
        self.client.headers['Content-Type'] = 'application/json'
        self.client_piano = PianoClient()
        self.marca = ''
        self.name_file = format_name_date()
        self.sku = []
        self.terms = dict()
        self.grant = dict()

        self.grant_ge = []
        self.grant_ce = []

        self.terms_ce = {'JKAO28': 'TMAEF17SD6RW'}
        self.terms_ge = {}

    def add_arguments(self, parser):
        parser.add_argument(
            "--marca",
            type=str,
            help="marca news")
        parser.add_argument(
            "--date_init",
            type=str,
            help="Fecha más antigua")
        parser.add_argument(
            '--date_end',
            type=str,
            help="Nombre de archivo que será creado")
        parser.add_argument(
            '--download',
            action='store_true',
            help='download report'
        )
        parser.add_argument(
            '--distinct',
            action='store_true',
            help='filter distinct subs id'
        )
        parser.add_argument(
            '--subs',
            action='store_true',
            help='download subs detail'
        )
        parser.add_argument(
            '--term',
            action='store_true',
            help='create terms csv'
        )

    def handle(self, *args, **options):
        if options.get("marca", None):
            self.client.headers['Arc-Site'] = options.get("marca", None)
            self.client_piano.headers['Arc-Site'] = options.get("marca", None)
            if options.get("marca", None) == 'gestion':
                print('Terms Gestion')
                self.terms = self.terms_ge
                self.grant = self.grant_ge
            elif options.get("marca", None) == 'elcomercio':
                print('Terms ElComercio')
                self.terms = self.terms_ce
                self.grant = self.grant_ce

        dir_path_cortesia = os.path.join(self.path, f'subs-{self.name_file}')
        self.path_subs = os.path.join(self.path, f'subs-08-07-2022_15-54-24-ce-all-subs')
        if not os.path.exists(self.path_subs):
            os.mkdir(self.path_subs)

        self.path_subs_details = f"{self.path_subs}/detail_files"
        if not os.path.exists(self.path_subs_details):
            os.mkdir(self.path_subs_details)

        if options["date_init"] is not None and options["date_end"] is not None:
            date_init = options["date_init"]
            date_end = options["date_end"]
            self.create_arc_report_job_ids(date_init, date_end)
            self.download_sale_report()
            self.distinct_sale_report()
            self.download_subs_detail()
            self.create_terms_csv()
        else:
            if options['download']:
                self.download_sale_report()
            if options['distinct']:
                self.distinct_sale_report()
            if options['subs']:
                self.download_subs_detail()
            if options['term']:
                self.create_terms_csv()

    def create_arc_report_job_ids(self, di, de):
        name = '01_arc_sale_jobIDs.csv'
        job_ids_path = f"{self.path_subs}/{name}"
        info_file_path = f"{self.path_subs}/00_{di}--{de}.txt"
        di, de = period_dates_for_report(di, de)

        with open(info_file_path, "w", encoding="utf-8") as a_outfile:
            a_outfile.write('\n')

        with open(job_ids_path, "w", encoding="utf-8") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['jobID'])
            for dates in form_date_ranges(di, de):
                report_id = self.client.create_sale_report(dates[0], dates[1])
                writer.writerow([report_id])
        return name

    def download_sale_report(self):
        name_job_ids = '01_arc_sale_jobIDs.csv'
        name_download_sale = '02_arc_sale_download.json'
        job_ids_path = f'{self.path_subs}/{name_job_ids}'
        download_sale_path = f'{self.path_subs}/{name_download_sale}'

        df = pd.read_csv(job_ids_path)
        list_job_ids = df["jobID"].to_list()
        num_reports_ids = len(list_job_ids)
        num_reports_downloaded = 0

        with open(download_sale_path, "w", encoding="utf-8") as outfile:
            outfile.write('[\n')
            for report_id in list_job_ids:
                print(report_id)
                num_reports_downloaded += 1
                print(f"process download: "
                      f"{num_reports_ids}/{num_reports_downloaded}",
                      end='\r', flush=True)
                reports = recu_download_report(self.client, report_id)
                if reports is None:
                    reports = recu_download_report(self.client, report_id)
                num_report = 0
                for report in reports:
                    num_report += 1
                    if num_reports_downloaded == 1 and num_report == 1:
                        outfile.write(f"{json.dumps(report, indent=4)}\n")
                    else:
                        outfile.write(f",{json.dumps(report, indent=4)}\n")
            outfile.write(']\n')
        return name_download_sale

    def distinct_sale_report(self):
        name_sale_download = '02_arc_sale_download.json'
        name_sale_distinct = '03_arc_sale_distinct_download.json'
        file_to_read_path = f"{self.path_subs}/{name_sale_download}"
        file_to_write_path = f"{self.path_subs}/{name_sale_distinct}"
        subs_ids = list()
        num_report = 0
        with open(file_to_read_path, 'r', encoding='utf-8') as readfile:
            subs = json.load(readfile)
        print(f"Nº de elementos en 02_arc_sale_download: {len(subs)}")
        with open(file_to_write_path, 'w', encoding='utf-8') as outfile:
            outfile.write('[')
            terms_all = self.grant + list(self.terms.keys())
            for sub in subs:
                if sub.get('currentProductPriceCode', '') in terms_all :
                    if sub['subscriptionId'] in subs_ids:
                        continue
                    subs_ids.append(sub['subscriptionId'])
                    num_report += 1
                    if num_report == 1:
                        outfile.write(f"{json.dumps(sub, indent=4)}\n")
                    else:
                        outfile.write(f",{json.dumps(sub, indent=4)}\n")
            outfile.write(']')
        print(f"Nº de elementos en 03_arc_sale_distinct_download: {num_report}")

    def download_subs_detail(self):
        name_sale_distinct = '03_arc_sale_distinct_download.json'
        name_sale_detail = '04_arc_sale_subs_detail.json'
        file_to_read_path = f"{self.path_subs}/{name_sale_distinct}"
        with open(file_to_read_path, 'r', encoding='utf-8') as file:
            subs = json.load(file)
        print(f"Nº 03_arc_sale_distinct_download {len(subs)}")
        thread_files(self.client, subs, self.path_subs, self.path_subs_details,
                     'arc_sale_subs_detail')

    def create_terms_csv(self):
        name_sale_detail = '04_arc_sale_subs_detail.json'
        name_term_csv = 'custom_terms.csv'
        grant_access_csv = 'grant_access.csv'
        bundle_access_csv = 'bundle_access.csv'
        file_to_read_path = f'{self.path_subs}/{name_sale_detail}'
        file_to_write_path = f'{self.path_subs}/{name_term_csv}'
        file_gran_access_path = f'{self.path_subs}/{grant_access_csv}'
        file_bundle_access_path = f'{self.path_subs}/{bundle_access_csv}'

        with open(file_to_read_path, 'r', encoding='utf-8') as readfile:
            subs = json.load(readfile)

        with open(file_to_write_path, 'w', encoding='utf-8') as file_csv,\
                open(file_gran_access_path, 'w', encoding='utf-8') as grant_access_file,\
                open(file_bundle_access_path, 'w', encoding='utf-8') as bundle_access_file:
            write = csv.writer(file_csv)  # terms_file
            grant_access_write = csv.writer(grant_access_file)

            header_row = ['user_id', 'term_id', 'access_end_date',
                          'unlimited_access']

            write.writerow(header_row)

            bundle_access_write = csv.writer(bundle_access_file)
            bundle_access_write.writerow(['sku', 'price_code',
                                          'subscription_id_arc', 'term_id',
                                          'access_id'])

            grant_access_write.writerow(['clientID', 'sku', 'pricecode'])
            subs_ids = list()
            num_subs = 0
            for sub in subs:
                if sub.get('sku') in self.sku:
                    date = sub.get('nextEventDateUTC', '')
                    access_end_date, unlimited_access = self.time_access(date)
                    self.client_piano.custom_create(sub.get('clientID', ''),
                                                    self.terms[
                                                        sub.get('sku', '')],
                                                    access_end_date,
                                                    unlimited_access)
                    bundle_access_write.writerow([sub.get('sku', ''),
                                                  sub.get('priceCode', ''),
                                                  sub.get('subscriptionID', ''),
                                                  '', ''])
                    continue
                if (sub.get('priceCode', '') in self.grant and
                        self.is_active_sub(sub)):
                    grant_access_write.writerow([sub.get('clientID'),
                                                 sub.get('sku')])
                    continue
                if self.is_free_or_linked(sub) and self.is_active_sub(sub):
                    try:
                        term_id = self.terms[sub.get('priceCode')]
                    except Exception as e:
                        continue
                    user_id = sub.get('clientID')
                    date = sub.get('nextEventDateUTC', '')
                    access_end_date, unlimited_access = self.time_access(date)
                    write.writerow([user_id,
                                    term_id,
                                    access_end_date,
                                    unlimited_access])
                    num_subs += 1
                    subs_ids.append(sub.get('subscriptionID'))
            print(f"Nº 04_arc_sale_subs_detail: {num_subs}")

    @staticmethod
    def is_free_or_linked(sub):
        if sub['currentPaymentMethod']['paymentPartner'] in ['Linked', 'Free']:
            return True
        else:
            return False

    @staticmethod
    def is_active_sub(sub):
        if sub.get('status', 0) == 1:
            return True
        else:
            return False

    @staticmethod
    def time_access(date):
        access_end_date = ''
        unlimited_access = 'true'
        if date != '' or date is not None:
            date = time_to_term(date)
            if date.year <= 2030:
                unlimited_access = 'false'
                access_end_date = str(date.strftime("%m/%d/%Y %H:%M"))
            return access_end_date, unlimited_access
        else:
            return access_end_date, unlimited_access


def time_to_term(date):
    try:
        return timestamp_to_datetime(date)
    except Exception as e:
        return e


def timestamp_to_datetime(timestamp):
    if isinstance(timestamp, str):
        timestamp = int(timestamp)

    if isinstance(timestamp, int):
        return datetime.fromtimestamp(
            timestamp / 1000,
            tz=get_default_timezone()
        )


def recu_download_report(client, report_id):
    try:
        reports = client.download_sale_report(report_id)
        return reports
    except Exception as e:
        recu_download_report(client, report_id)
        print(e)


def generate_file(client, file_path, subs, index, number_of_file):
    with open(file_path, 'w', encoding='utf-8') as file_subs:
        # file_subs.write('[')
        for i, sub in enumerate(subs, start=index):
            print(f"{i}", end='\r', flush=True)
            file_subs.write(
                get_subscription(
                    client, i, sub['subscriptionId']))
        # file_subs.write(']')


def get_subscription(client, index, subs_id):
    if index != 1:
        return (f",\n"
                f"{json.dumps(client.get_subscription(subs_id), indent=4)}")
    else:
        return f"{json.dumps(client.get_subscription(subs_id), indent=4)}"


def thread_files(client, list_objs, name_subs, name_dir, name_file):
    len_objs = len(list_objs)
    number_of_file = 0
    after_len_uuids = 0
    list_thread = list()
    while after_len_uuids <= len_objs:
        number_of_file += 1
        before_len_uuids = after_len_uuids
        after_len_uuids += 1000

        path = f"{name_dir}/{name_file}_{number_of_file}.json"

        if after_len_uuids >= len_objs:
            # print(f"{before_len_uuids}:")
            index = before_len_uuids + 1
            list_uuids = list_objs[before_len_uuids:]
        else:
            # print(f"{before_len_uuids}:{after_len_uuids}")
            index = before_len_uuids + 1
            list_uuids = list_objs[before_len_uuids:after_len_uuids]
        t = threading.Thread(
            target=generate_file,
            args=(client, path, list_uuids, index, number_of_file))
        t.start()
        list_thread.append(t)
    for l in list_thread:
        l.join()
    join_files(name_subs, 'detail_files', '04_arc_sale_subs_detail.json')
