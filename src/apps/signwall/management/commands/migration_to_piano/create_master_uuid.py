import csv


def create_master_uuid(profiles, path):
    length_uuids = len(profiles)
    count_user_finish = 0
    headers = ["user_id"]
    with open(path, "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)
        for profile in profiles:
            row = list()
            try:
                row.append(profile.get('uuid', ''))
                writer.writerow(row)
                count_user_finish += 1
                print(f"{length_uuids}/{count_user_finish}", end='\r', flush=True)
            except Exception as e:
                raise e

