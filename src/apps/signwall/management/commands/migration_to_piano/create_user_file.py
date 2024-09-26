import csv

from .utils import convert_identities_to_social_account, get_or_blank


def create_file_user(profiles, path):
    length_uuids = len(profiles)
    count_user_finish = 0
    headers = ["user_id", "email", "first_name", "last_name", "password",
               "social_accounts"]
    with open(path, "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)

        for profile in profiles:
            row = list()
            email_user = str(profile.get('email', ''))
            try:
                row.append(profile.get('uuid', ''))
                identities = convert_identities_to_social_account(
                    profile.get("identities", list())
                )
                if email_user in ['', None, 'None'] or \
                        email_user.split('@')[1] in ['facebook.com', 'googlemail.com']:
                    if identities:
                        single = identities.split(';')[0].split(':')
                        type_name = single[0].lower()
                        type_id = single[1]
                        row.append(f'social-{type_id}@{type_name}.com')
                    else:
                        row.append(str(profile.get('email', '')))
                else:
                    row.append(str(profile.get('email', '')))
                row.append(get_or_blank(profile.get('firstName', '')))
                row.append(get_or_blank(profile.get('lastName', '')))
                row.append(":UNKNOWN:::0")
                row.append(identities)
                writer.writerow(row)
                count_user_finish += 1
                print(f"{length_uuids}/{count_user_finish}", end='\r', flush=True)
            except Exception as e:
                raise e
