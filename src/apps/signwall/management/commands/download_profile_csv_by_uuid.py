from datetime import datetime, timedelta
import time
import csv

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.arcsubs.arcclient import ArcClientAPI


class Command(BaseCommand):
    help = ("Exporta uuid de usuarios para migración a piano",)

    def handle(self, *args, **options):
        client = ArcClientAPI()

        with open('/home/milei/Escritorio/eli/test.csv') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                profile = client.get_profile_by_uuid(row[2])
                fields = list(profile['fields'].values())
                print(fields)   


