import csv
import datetime
import json
import os

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.arcsubs.arcclient import ArcClientAPI
from .migration_to_piano.create_arc_reports import (
    create_arc_report_job_ids, create_file_download_report,
    create_file_profiles)
from .migration_to_piano.create_consent_file import create_file_consent
from .migration_to_piano.create_custom_file import create_file_custom
from .migration_to_piano.create_master_uuid import create_master_uuid
from .migration_to_piano.create_user_file import create_file_user
from .migration_to_piano.utils import format_name_date, has_attributes, \
    has_email, is_active_user, timestamp_to_datetime, convert_bool, \
    get_attributes, join_files, convert_uuids_to_list


def name_files_piano(aid):
    file_user = f'{aid}_users.csv'
    file_consent = f'{aid}_consent_fields.csv'
    file_custom = f'{aid}_custom_fields.csv'
    file_term = f'{aid}_custom_term.csv'
    file_uuids = f'{aid}_uuids.csv'
    return file_user, file_consent, file_custom, file_term, file_uuids


def step_01_job_ids(options,  path, client):
    date_init = options["date_init"]
    date_end = options["date_end"]
    file_job_ids = create_arc_report_job_ids(
        date_init, date_end, path, client)
    return file_job_ids


def is_activate_in_range(profile):
    user_identities = profile.get('identities', None)
    if user_identities:
        count_user_identities = len(user_identities)
        if count_user_identities == 1:
            if user_identities[0]['lastLoginDate']:
                date_ll = timestamp_to_datetime(
                    user_identities[0]['lastLoginDate'])
                return is_active_user(date_ll)
            else:
                return False
        else:
            list_dates_identities = list()
            for identity in user_identities:
                if identity['lastLoginDate']:
                    date_last_login = timestamp_to_datetime(
                        identity['lastLoginDate'])
                    list_dates_identities.append(date_last_login)
            if len(list_dates_identities) == 0:
                return False
            elif len(list_dates_identities) == 1:
                return is_active_user(list_dates_identities[0])
            else:
                date_now = datetime.datetime.now() + \
                           datetime.timedelta(days=1)
                start_date = datetime.datetime.strptime('1/1/2019', '%m/%d/%Y')
                end_date = date_now
                in_between_dates = []
                for d in list_dates_identities:
                    if start_date <= d <= end_date:
                        in_between_dates.append(d)
                date_ll = in_between_dates[-1]
                return is_active_user(date_ll)
    else:
        return False


def validation_user(profile):
    if profile is None:
        print(f"not profile")
        return False
    # if not is_activate_in_range(profile):
    #     print(f"not last login: {profile['uuid']}")
    #     return False
    # if has_email(profile) is False:
    #     print(f"not email: {profile['uuid']}")
    #     return False
    # if has_attributes(profile) is False:
    #     print(f"not attr: {profile['uuid']}")
        # return False
    # attribute = profile.get("attributes", [])
    # if convert_bool(get_attributes(attribute, 'data_treatment')) != 'true':
    #     print(f"not data_treatment: {profile['uuid']}")
    #     return False
    return True


def get_aid(options):
    if options["aid"] is not None:
        aid = options["aid"]
        return aid
    else:
        raise AttributeError("--aid need id de application")


def create_main_dir(options, main_path, marca, name_file):
    if options["main_dir"] is not None:
        main_dir_path = f"{main_path}/{options['main_dir']}"
    else:
        main_dir_path = os.path.join(main_path, f"{marca}-{name_file}")
        os.mkdir(main_dir_path)
    return main_dir_path


def create_sub_dir(options, main_path):
    if options["sub_dir"] is not None:
        sub_dir = options["sub_dir"]
        sub_dir_path = os.path.join(main_path, sub_dir)
        if not os.path.exists(sub_dir_path):
            os.mkdir(sub_dir_path)
        return sub_dir_path
    else:
        msg = '--sub_dir need define name of directory: sandbox_1, ' \
              'sandbox_2, production'
        raise AttributeError(msg)


def profiles_json_to_dict(path_for_file_profiles):
    with open(path_for_file_profiles, 'r', encoding='utf-8') as file:
        profiles = json.load(file)
        return profiles


class Command(BaseCommand):
    help = ("Exporta lista de usuarios para migración a piano",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = f"{settings.BASE_DIR}/reports_migration"
        self.marca = ""
        self.client = ArcClientAPI()
        self.name_file = format_name_date()
        self.file_job_ids = '01_arc_report_jobIDs.csv'
        self.file_download_report = '02_arc_report_download.json'
        self.file_profiles_report = 'profiles.json'

    def add_arguments(self, parser):
        parser.add_argument("--marca", type=str,
                            help="marca: gestion, peru21")
        parser.add_argument("--aid", type=str,
                            help="id application")

        parser.add_argument("--main_dir", type=str,
                            help=("define name of directory: "
                                  "peru21-02-03-2022_15-17-04"))
        parser.add_argument("--sub_dir", type=str,
                            help=("define name of directory: "
                                  "sandbox_1, sandbox_2, production"))

        parser.add_argument("--date_init", type=str,
                            help="Fecha más antigua")
        parser.add_argument('--date_end', type=str,
                            help="Fecha más reciente")

        parser.add_argument("--file_jobIDs_csv", action='store_true',
                            help="if true pass jobIDs process")
        parser.add_argument("--file_download_report", action='store_true',
                            help="if true pass download process")
        parser.add_argument("--file_profiles_report", action='store_true',
                            help="if true pass profiles process")
        parser.add_argument("--file_profiles_join", action='store_true',
                            help="join profiles")
        parser.add_argument("--file_by_uuid", action='store_true',
                            help="profiles byh uuid")

        parser.add_argument("--init_migration", action='store_true',
                            help="iniciar migración")

    def handle(self, *args, **options):
        self.marca = options["marca"]
        self.client.headers['Arc-Site'] = self.marca
        self.client.headers['Content-Type'] = 'application/json'

        file_user, file_consent, file_custom, file_term, file_uuids = \
            name_files_piano(get_aid(options))

        main_dir_path = create_main_dir(options, self.path, self.marca,
                                        self.name_file)

        sub_dir_path = create_sub_dir(options, main_dir_path)

        name_file_path_user = os.path.join(sub_dir_path, file_user)
        name_file_path_consent = os.path.join(sub_dir_path, file_consent)
        name_file_path_custom = os.path.join(sub_dir_path, file_custom)
        # name_file_path_term = os.path.join(sub_dir_path, file_term)
        name_file_master_uuid = os.path.join(sub_dir_path, file_uuids)
        if not options['file_by_uuid']:
            if not options["file_jobIDs_csv"]:
                self.file_job_ids = step_01_job_ids(options, main_dir_path,
                                                    self.client)

            if not options["file_download_report"]:
                df = pd.read_csv(f"{main_dir_path}/{self.file_job_ids}")
                list_job_ids = df["jobID"].to_list()
                self.file_download_report = create_file_download_report(
                    list_job_ids, main_dir_path, self.client)

            if not options["file_profiles_report"]:
                file_path = f"{main_dir_path}/{self.file_download_report}"
                with open(file_path, encoding='utf-8') as file:
                    profiles = json.load(file)
                    self.file_profiles_report = create_file_profiles(
                        profiles, main_dir_path, self.client)
        else:
            if not options['main_dir']:
                file_path = f"{self.path}/ByUuids2.csv"
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = csv.DictReader(file)
                    uuids = list()
                    for d in data:
                        uuids.append(d['uuid'])
                    data = list(set(uuids))

                    profiles = convert_uuids_to_list(data)
                    self.file_profiles_report = create_file_profiles(
                        profiles, main_dir_path, self.client)
        if options["file_profiles_join"]:
            join_files(main_dir_path, 'files_profile', 'profiles.json')

        path_for_file_profiles = f"{main_dir_path}/{self.file_profiles_report}"
        profiles = profiles_json_to_dict(path_for_file_profiles)

        length_uuids = len(profiles)
        count_valid = 0
        count_invalid = 0
        valid_users = list()

        for p in profiles:
            if validation_user(p):
                if p.get('uuid', '') == None:
                    continue
                count_valid += 1
                valid_users.append(p)
            else:
                count_invalid += 1

        print(f"Profiles total: {length_uuids}")
        print(f"Profiles available: {count_valid}")
        print(f"Profiles  not available: {count_invalid}")

        create_master_uuid(valid_users, name_file_master_uuid)
        create_file_user(valid_users, name_file_path_user)
        create_file_consent(valid_users, name_file_path_consent)
        create_file_custom(valid_users, name_file_path_custom, self.marca)


"""
        f = 0
        l = 0
        fl = 0
        if p.get('firstName', None) in [None, '']:
                f += 1
            if p.get('lastName', None) in [None, '']:
                l += 1
            if p.get('firstName', None) in [None, ''] and p.get('lastName', 
                None) in [None, '']:
                fl += 1
"""