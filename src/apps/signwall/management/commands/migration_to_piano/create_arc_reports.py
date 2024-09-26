import csv
import json
import os
import threading

from .utils import (form_date_ranges, is_active_user, has_email, has_attributes,
                    convert_bool, get_attributes, period_dates_for_report,
                    join_files)


def create_arc_report_job_ids(di, de, main_path, client):
    name = f"01_arc_report_jobIDs.csv"
    di, de = period_dates_for_report(di, de)

    file_path = f"{main_path}/{name}"
    info_file_path = f"{main_path}/00-detail_{di}--{de}.txt"

    with open(info_file_path, "w", encoding="utf-8") as outfile:
        outfile.write('[\n')

    with open(file_path, "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['jobID'])
        for dates in form_date_ranges(di, de):
            report_id = client.create_report(dates[0], dates[1])
            writer.writerow([report_id])
    return name


def create_file_download_report(list_reports_ids, main_path, client):
    total_reports_ids = len(list_reports_ids)
    num_report = 0
    num_reports_downloaded = 0
    name_file = "02_arc_report_download.json"
    path_download_report = f"{main_path}/{name_file}"
    with open(path_download_report, "w", encoding="utf-8") as outfile:
        outfile.write('[\n')
        for i, report_id in enumerate(list_reports_ids, 1):
            num_reports_downloaded += 1
            print(f"{total_reports_ids}/{i}", end='\r', flush=True)
            reports = client.download_report(report_id)
            num_report = 0
            for report in reports:
                if report.get('lastLoginDate', None):
                    if is_active_user(report.get('lastLoginDate')):
                        num_report += 1
                        if num_reports_downloaded == 1 and num_report == 1:
                            outfile.write(f"{json.dumps(report, indent=4)}\n")
                        else:
                            outfile.write(f",{json.dumps(report, indent=4)}\n")
        outfile.write(']\n')
        print(f"finish download report: {num_report}")
    return name_file


def create_file_profiles(list_objects, main_path, client):
    dir_path = os.path.join(main_path, 'files_profile')
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    thread_files(client, list_objects, main_path)
    return 'profiles.json'


def report_download_profiles(client, path, list_objects, index):
    len_profiles = len(list_objects)
    count_objects = 1
    with open(path, 'w', encoding='utf-8') as save_profile:
        for i, user in enumerate(list_objects, start=index):
            print(f"{len_profiles}/{count_objects}", end='\r', flush=True)
            uuid = user['clientId']
            try:
                profile = client.get_profile_by_uuid(uuid)
            except Exception as e:
                print(uuid)
            finally:
                if profile is not None:
                    if i == 1:
                        save_profile.write(f"{json.dumps(profile, indent=4)}")
                    else:
                        save_profile.write(f",{json.dumps(profile, indent=4)}")
                else:
                    print(uuid)
            count_objects += 1


def thread_files(client, list_objs, root_path):
    len_objs = len(list_objs)
    number_of_file = 0
    after_len_uuids = 0
    list_thread = list()

    name_dir = f"{root_path}/files_profile"
    name_file = 'all_profiles'
    while after_len_uuids <= len_objs:
        number_of_file += 1
        before_len_uuids = after_len_uuids
        after_len_uuids += 9000
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
            target=report_download_profiles,
            args=(client, path, list_uuids, index))
        t.start()
        list_thread.append(t)
    for l in list_thread:
        l.join()
    join_files(root_path, 'files_profile', 'profiles.json')
