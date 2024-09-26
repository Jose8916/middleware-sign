import csv

from .utils import (get_or_blank, timestamp_to_date, format_gender,
                    format_birthday, contact_phone, user_verified, from_source,
                    old_subs, get_attributes, only_letters_for_name)


def build_row(profile, marca):
    attribute = profile.get("attributes", [])
    row = list()
    row.append(profile.get('uuid', None))
    row.append(only_letters_for_name(get_or_blank(profile.get('secondLastName'))))
    row.append(timestamp_to_date(profile.get('createdOn')))
    row.append(timestamp_to_date(profile.get('modifiedOn')))
    row.append(format_gender(profile.get('gender', None)))
    row.append(format_birthday(profile))
    row.append(get_or_blank(profile.get('picture', None)))
    if profile.get('contacts', None):
        row.append(contact_phone(profile.get('contacts')[0]['phone']))
    else:
        row.append('')
    row.append(user_verified(  # email_verified
        profile.get('emailVerified', None),
        profile.get('mppVerified', None)))
    row.append((old_subs(profile.get('uuid', None), marca)))  # old_subscriber
    row.append(from_source(attribute))  # source
    row.append(get_attributes(attribute, 'origin_domain'))
    row.append(get_attributes(attribute, 'origin_referer'))
    row.append(get_attributes(attribute, 'origin_method'))
    row.append(get_attributes(attribute, 'origin_device'))
    row.append(get_attributes(attribute, 'origin_action'))
    row.append(get_attributes(attribute, 'origin_user_agent'))
    row.append(get_attributes(attribute, 'old_email_hash'))
    row.append(get_attributes(attribute, 'email_hash'))
    row.append(get_attributes(attribute, 'civil_status'))
    row.append(get_attributes(attribute, 'document_type'))
    row.append(get_attributes(attribute, 'document_number'))
    row.append(get_attributes(attribute, 'country_code'))
    row.append(get_attributes(attribute, 'province_code'))
    row.append(get_attributes(attribute, 'departament_code'))
    row.append(get_attributes(attribute, 'district_code'))
    return row


def create_file_custom(profiles, path, marca):
    headers = [
        "user_id", "second_last_name", "create_date",
        "update_date", "gender", "birthday",
        "profile_image", "contact_phone",
        "email_verified", "old_subscriber", "source",
        "origin_domain", "origin_referer",
        "origin_method",
        "origin_device", "origin_action",
        "origin_user_agent",
        "old_email_hash", "email_hash",
        "civil_status",
        "document_type", "document_number",
        "country_code", "province_code",
        "departament_code", "district_code"]
    length_uuids = len(profiles)
    try:
        with open(path, "w", encoding="utf-8") as custom_file:
            writer = csv.writer(custom_file)
            writer.writerow(headers)
            for index, profile in enumerate(profiles, 1):
                row = build_row(profile, marca)
                writer.writerow(row)
                print(f"{length_uuids}/{index}", end='\r', flush=True)
    except Exception as e:
        raise e
