import math
import os
import re
from datetime import datetime, timedelta

from apps.arcsubs.arcclient import IdentityClient


def format_name_date():
    return datetime.strftime(datetime.now(), '%d-%m-%Y_%H-%M-%S')


def form_date_ranges(di, de):
    raw_count_weeks = (de - di).days / 7
    rounded_count_weeks = abs(math.ceil((de - di).days / 7))
    count_total_weeks = rounded_count_weeks
    dates_for_report = list()

    print(di)
    print(de)
    print(raw_count_weeks)
    print(rounded_count_weeks)

    backi = di
    backe = de
    if raw_count_weeks <= 1:
        date_init = f"{di.date()}T{di.time()}.000Z"
        date_end = f"{de.date()}T{de.time()}.000Z"
        dates_for_report.append([date_init, date_end])
    else:
        count_weeks = 0
        for _ in range(rounded_count_weeks):
            count_weeks += 1
            backi = backe - timedelta(days=7)
            if count_weeks < count_total_weeks:
                date_init = f"{backi.date()}T{backi.time()}.000Z"
                date_end = f"{backe.date()}T{backe.time()}.000Z"
                dates_for_report.append([date_init, date_end])
            else:
                date_init = f"{di.date()}T{di.time()}.000Z"
                date_end = f"{backe.date()}T{backe.time()}.000Z"
                dates_for_report.append([date_init, date_end])
            backe = backi
    return dates_for_report


def period_dates_for_report(date_init, date_end):
    # date_init = '2018-01-20'
    # date_end = '2022-01-23'
    di = datetime.strptime(date_init, "%Y-%m-%d:%H-%M-%S")
    di = di + timedelta(hours=5)
    de = datetime.strptime(date_end, "%Y-%m-%d:%H-%M-%S")
    de = de + timedelta(hours=5)
    return di, de


def is_active_user(date):
    if date:
        d1 = datetime.now().date()
        if type(date) is str:
            d2 = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").date()
        else:
            d2 = date.date()
        total_days = abs((d1 - d2).days)
        return True if total_days <= 366 else False
    return False


def has_email(profile):
    return profile.get('email') if profile.get('email', False) else False


def has_true_data_treatment(profile):
    attributes = profile.get("attributes", [])

    if not has_attributes(attributes):
        return False
    attr_value = get_attributes(attributes, 'data_treatment')
    if convert_bool(attr_value) == "true":
        return True
    else:
        return False


def has_attributes(profile):
    attribute = profile.get("attributes", [])
    if attribute is None or attribute is False:
        return False
    else:
        return True


def get_attributes(attributes, search):
    if not attributes:
        return ''
    if search == 'data_treatment':
        search = "dataTreatment"
    if search == 'terms_and_privacy_policy':
        search = 'termsCondPrivaPoli'
    if search == 'origin_domain':
        search = "originDomain"
    if search == 'origin_referer':
        search = 'originReferer'
    if search == 'origin_method':
        search = 'originMethod'
    if search == 'origin_device':
        search = 'originDevice'
    if search == 'origin_action':
        search = 'originAction'
    if search == 'origin_user_agent':
        search = 'originUserAgent'

    if search == 'email_hash':
        search = 'emailHash'
    if search == 'old_email_hash':
        search = 'oldEmailHash'

    if search == 'civil_status':
        search = 'civilStatus'

    if search == 'document_type':
        search = 'documentType'
    if search == 'document_number':
        search = 'documentNumber'

    if search == 'country_code':
        search = 'country'
    if search == 'province_code':
        search = 'province'
    if search == 'departament_code':
        search = 'department'
    if search == 'district_code':
        search = 'district'

    for attribute in attributes:
        if search in list(attribute.values()):
            if search == 'originMethod':
                if attribute['value'] in ['1', '2', '5']:
                    if attribute['value'] == '1':
                        return '["Password"]'
                    elif attribute['value'] == '2':
                        return '["Facebook"]'
                    elif attribute['value'] == '5':
                        return '["Google"]'
                    else:
                        return ''
                else:
                    return ''
            if search == 'originDevice':
                if attribute['value'] == 'movil':
                    return '["mobile"]'
                else:
                    return f'["{attribute["value"]}"]'
            if search == "originAction":
                actions = ['authfia', 'landing', 'mailing',  'premium',
                           'relogin', 'resetpass', 'students', 'verify']
                if attribute['value'] in actions:
                    return f'["{attribute["value"]}"]'
                else:
                    return ''
            if search == 'originUserAgent':
                return

            if search == 'originDomain':
                return

            if search == 'civilStatus':
                if attribute['value'] == 'SO':
                    return '["Soltero(a)"]'
                elif attribute['value'] == 'CA':
                    return '["Casado(a)"]'
                elif attribute['value'] == 'DI':
                    return '["Divorciado(a)"]'
                elif attribute['value'] == 'VI':
                    return '["Viudo(a)"]'
                else:
                    return ''
            if search in ['country', 'province', 'department', 'district']:
                try:
                    return int(attribute['value'])
                except:
                    return ''
            if search == 'documentType':
                return f'["{attribute["value"]}"]'
            return attribute['value']
    return ''


def convert_bool(value):
    options_true = [1, "1", "true", True]

    if type(value) is str:
        value = value.lower()

    if value in options_true:
        return "true"
    else:
        return "false"


def convert_identities_to_social_account(identities):
    arc_social_accounts = list()
    for identity in identities:
        if identity['type'].upper() in ['FACEBOOK', 'GOOGLE', 'TWITTER',
                                        'LINKEDIN', 'APPLE']:
            arc_social_accounts.append(
                f"{identity['type'].upper()}:{identity['userName']}")
    return ";".join(arc_social_accounts)


def get_or_blank(value):
    return value if value else ""


def only_letters_for_name(value):
    name = list()
    for v in value:
        if v.isalpha() or v == ' ':
            name.append(v)
    return ''.join(name)


def timestamp_to_date(value):
    return datetime.fromtimestamp(int(value) / 1000.0).date()


def timestamp_to_datetime(value):
    return datetime.fromtimestamp(int(value) / 1000.0)


def format_gender(value):
    if value in ["MALE", "FEMALE"]:
        if value == 'MALE':
            return '["Hombre"]'
        elif value == 'FEMALE':
            return '["Mujer"]'
        else:
            return ""
    else:
        return ""


def format_birthday(profile):
    if profile.get('birthYear', None) is not None and \
            profile.get('birthMonth', None) is not None and \
            profile.get('birthDay', None) is not None:
        date = f"{profile.get('birthYear')}-{profile.get('birthMonth')}-{profile.get('birthDay')}"
        date = datetime.strptime(date, '%Y-%m-%d')
        return date.strftime('%Y-%m-%d')
    else:
        return ""


def contact_phone(value):
    if value not in ["undefined", "", None]:
        return re.search(r'\d+', value).group()
    else:
        return ""


def user_verified(a, b):
    if a or b:
        return 'true'
    else:
        return 'false'


def old_subs(value, marca):
    try:
        data = IdentityClient().get_subscriptions_by_user(marca, value)
        if len(data) > 0:
            return 'true'
        else:
            return 'false'
    except Exception as e:
        return 'false'


def from_source(attributes):
    if attributes:
        from_mpp = get_attributes(attributes, 'fromMPP')
        from_ecoid = get_attributes(attributes, 'fromEcoid')
        if from_mpp == '1' and (from_ecoid == '0' or from_ecoid == ''):
            return '["MPP"]'
        elif from_ecoid == '1' and (from_mpp == '0' or from_mpp == ''):
            return '["ECOID"]'
        return '["ARC"]'
    return '["ARC"]'


def join_files(path, dir_files, name_finale_file):
    main_directory = f"{path}/{dir_files}"
    files = os.listdir(main_directory)
    files = sorted(files)
    final_file = f"{path}/{name_finale_file}"
    with open(final_file, '+w', encoding='utf-8') as writefile:
        writefile.write('[\n')
        for file in files:
            with open(main_directory + '/' + file, 'r',
                      encoding='utf-8') as readfile:
                writefile.write(readfile.read())
        writefile.write('\n]')


def convert_uuids_to_list(uuids):
    list_objects = list()
    for uuid in uuids:
        list_objects.append({'clientId': uuid})
    return list_objects
