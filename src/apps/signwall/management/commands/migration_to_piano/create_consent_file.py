import csv

from .utils import convert_bool, get_attributes


def create_file_consent(profiles, path):
    length_uuids = len(profiles)
    count_user_finish = 0
    field_id = ['data_treatment', 'terms_and_privacy_policy']
    headers = ['user_id', 'field_id', 'checked']
    try:
        with open(path, "w", encoding="utf-8") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(headers)
            for profile in profiles:
                count_user_finish += 1
                for field in field_id:
                    row = list()
                    row.append(profile.get('uuid', ''))
                    row.append(field)

                    attribute = profile.get("attributes", [])
                    if attribute:
                        row.append(convert_bool(
                            get_attributes(attribute,
                                           field)))

                    else:
                        row.append('false')
                    writer.writerow(row)
                count_user_finish += 1
                print(f"{length_uuids}/{count_user_finish}", end='\r', flush=True)
    except Exception as e:
        raise e