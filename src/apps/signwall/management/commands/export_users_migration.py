import os
import sys
import time
from datetime import date, datetime

import pandas as pd
from apps.arcsubs.arcclient import ArcClientAPI  # arc identity/api
from apps.arcsubs.models import ArcUser  # middleware
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.aggregates import Count

today = str(date.today())


class Command(BaseCommand):
    help = ("Exporta lista de usuarios para migración a piano", )

    def add_arguments(self, parser):

        # To run for one ser with uuid
        parser.add_argument(
            "--url",
            default="",
            help=("Indique la lista de uuids."),
        )

    def handle(self, *args, **options):

        url = options["url"]
        current_file = __file__.rsplit("/", 1)[1].split(".")[0]

        df = pd.read_csv(url)
        arc_uuids = []
        arc_emails = []
        arc_first_names = []
        arc_last_names = []
        arc_social_accounts = []
        arc_passwords = []

        # extra
        list_arc_birth_day=[]
        list_arc_birth_month=[]
        list_arc_birth_year=[]
        list_arc_picture_url=[]
        list_arc_create_on=[]
        list_arc_gender=[]
        list_arc_phone=[]
        list_arc_contacts=[]
        list_arc_district=[]
        list_arc_province=[]
        list_arc_country=[]
        list_arc_department=[]

        # attributes
        list_arc_origin_domain = []
        list_arc_origin_referer = []
        list_arc_origin_device = []
        list_arc_terms_cond_priva_poli = []
        list_arc_data_treatment = []
        list_arc_civil_status = []
        list_arc_document_type = []
        list_arc_document_number = []

        print(f"\n[{current_file}] ARC -------------------------------------")
        for identity_uuid in df["uuid"].to_list():
            print(identity_uuid, end=' - ')
            try:
                # normal csv
                client = ArcClientAPI()
                profile = client.get_profile_by_uuid(identity_uuid)
                if profile==None:
                    print("No existe")
                    
                elif profile!=None:
                    arc_uuid = str(profile.get("uuid",""))
                    arc_email = str(profile.get("email",""))
                    arc_first_name = str(profile.get("firstName",""))
                    arc_last_name = str(profile.get("lastName",""))
                    arc_identities = profile.get("identities",[])
                    if arc_identities != []:
                        if len(arc_identities) > 0:
                            arc_social_account = str(
                                arc_identities[0]["userName"]
                            )  # only get the first associated account
                        else:
                            arc_social_account = str(
                                arc_identities["userName"]
                            )  # only get the first associated account
                    else:
                        arc_social_account = ""

                    arc_uuids.append(arc_uuid)
                    arc_emails.append(arc_email)
                    arc_first_names.append(arc_first_name)
                    arc_last_names.append(arc_last_name)
                    arc_social_accounts.append(arc_social_account)
                    arc_passwords.append(':UNKNOWN:::0')

                    # extra data
                    arc_birth_day = str(profile.get("birthDay",""))
                    arc_birth_month = str(profile.get("birthMonth",""))
                    arc_birth_year = str(profile.get("birthYear",""))
                    arc_picture = str(profile.get("picture",""))
                    arc_create_on = str(profile.get("createOn",""))

                    arc_gender = str(profile.get("gender",""))
                    arc_phone = str(profile.get("phone",""))
                    arc_contacts = profile.get("contacts",[])
                    if arc_contacts!=None:
                        if len(arc_contacts) > 0:
                            arc_contacts = arc_contacts[0].get("phone","")
                    arc_district = str(profile.get("district",""))
                    arc_province = str(profile.get("province",""))
                    arc_country = str(profile.get("country",""))
                    arc_department = str(profile.get("department",""))


                    # attributes
                    arc_attributes = profile.get("attributes",{})
                    arc_origin_domain = ""
                    arc_origin_referer = ""
                    arc_origin_device = ""
                    arc_terms_cond_priva_poli = ""
                    arc_data_treatment = ""
                    arc_civil_status = ""
                    arc_document_type = ""
                    arc_document_number = ""

                    for item in arc_attributes:

                        new_column = item.get("item")
                        new_value = item.get("value")

                        if new_column == "originDomain":
                            arc_origin_domain = str(new_value)  # atributes
                        if new_column == "originReferer":
                            arc_origin_referer = str(new_value)
                        if new_column == "originDevice":
                            arc_origin_device = str(new_value)
                        if new_column == "termsCondPrivaPoli":
                            arc_terms_cond_priva_poli = str(new_value)
                        if new_column == "dataTreatment":
                            arc_data_treatment = str(new_value)
                        if new_column == "civilStatus":
                            arc_civil_status = str(new_value)  # atributes
                        if new_column == "documentType":
                            arc_document_type = str(new_value)  # atributes
                        if new_column == "documentNumber":
                            arc_document_number = str(new_value)  # atributes


                    list_arc_birth_day.append(arc_birth_day)
                    list_arc_birth_month.append(arc_birth_month)
                    list_arc_birth_year.append(arc_birth_year)
                    list_arc_picture_url.append(arc_picture)
                    list_arc_create_on.append(arc_create_on)
                    list_arc_gender.append(arc_gender)
                    list_arc_phone.append(arc_phone)
                    list_arc_contacts.append(arc_contacts)
                    list_arc_district.append(arc_district)
                    list_arc_province.append(arc_province)
                    list_arc_country.append(arc_country)
                    list_arc_department.append(arc_department)

                    # attributes
                    list_arc_origin_domain.append(arc_origin_domain)
                    list_arc_origin_referer.append(arc_origin_referer)
                    list_arc_origin_device.append(arc_origin_device)
                    list_arc_terms_cond_priva_poli.append(arc_terms_cond_priva_poli)
                    list_arc_data_treatment.append(arc_data_treatment)
                    list_arc_civil_status.append(arc_civil_status)
                    list_arc_document_type.append(arc_document_type)
                    list_arc_document_number.append(arc_document_number)
            except Exception as e:
                print(e)

        print(
            f"\n[{current_file}] DATAFRAME-------------------------------------"
        )
        df = pd.DataFrame(list(
            zip(arc_uuids, 
                arc_emails, 
                arc_first_names,
                arc_last_names,
                arc_passwords, 
                arc_social_accounts)),
                          columns=[
                              'user_id', 'email', 'first_name', 'last_name',
                              'password', 'social_accounts'
                          ])
        df.fillna("",inplace=True)
        df.to_csv("migration_piano.csv", index=False)
        print(df)

        print("data migrated to --- migration_piano.csv")

        print(
            f"\n[{current_file}] DATAFRAME EXTRA-------------------------------------"
        )

        df = pd.DataFrame(list(
            zip(arc_uuids,
            list_arc_birth_day,
            list_arc_birth_month,
            list_arc_birth_year,
            list_arc_picture_url,
            list_arc_create_on,
            list_arc_gender,
            list_arc_phone,
            list_arc_contacts,
            list_arc_district,
            list_arc_province,
            list_arc_country,
            list_arc_department,
            list_arc_origin_domain,
            list_arc_origin_referer,
            list_arc_origin_device,
            list_arc_terms_cond_priva_poli,
            list_arc_data_treatment,
            list_arc_civil_status,
            list_arc_document_type,
            list_arc_document_number)),
                          columns=[
                              'user_id', 
                              'birth_day',
                              'birth_month',
                              'birth_year',
                              'picture',
                              'create_on',
                              'gender',
                              'phone',
                              'contacts',
                              'district',
                              'province',
                              'country',
                              'department',
                              'origin_domain',
                              'origin_referer',
                              'origin_device',
                              'terms_cond_priva_poli',
                              'data_treatment',
                              'civil_status',
                              'document_type',
                              'document_number',
                          ])
        df.fillna("",inplace=True)
        df.to_csv("migration_piano_extra.csv", index=False)
        print(df)   

        print("data migrated to --- migration_piano_extra.csv")
        print(
            f"\n[{current_file}] FINISH-------------------------------------")
