# -*- coding: utf-8 -*-
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import datetime
from ...models import DeleteUser, ArcUser
from datetime import date, datetime, timedelta
from os import path
import csv
import pytz
import requests


class Command(BaseCommand):
    help = 'Ejecuta el comando'

    def handle(self, *args, **options):

        startdate = date(2012, 12, 11)
        enddate = datetime.now(pytz.timezone('America/Lima'))

        users = ArcUser.objects.filter(
            email__contains='mailinator.com'
        ).exclude(
            with_activity=True,
            with_subscription=True,
            created_on__range=[startdate, enddate]
        )
        for user in users:
            self.send_request(user.uuid)

        return 'Ejecucion exitosa'

        # self.send_request()
        self.approve_request()

    def send_request(self):
        domain = 'https://sandbox.elcomercio.arcpublishing.com/identity/private/v1/task'
        headers = {
            "accept": "application/json",
            "accept-language": "es-ES,es;q=0.9,en;q=0.8",
            "arc-site": "elcomercio",
            "content-type": "application/json",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        }
        cookies = {
            'Arc-Token': 'eyJpYXQiOjE1OTQ2NTI3MDMuMzcxLCJpc3MiOiJTQU1MMi9lbGNvbWVyY2lvIiwic3ViIjp7ImUiOiJqbWFjaGljYWRvQHJtZ3BlcnVzdGFmZi5jb20iLCJkIjoiSmF2aWVyIE1hY2hpY2FkbyIsImciOlsiREVWIEFkbWluIiwiRXZlcnlvbmUiLCJERVYgU1VTQyIsIlNVU0MgQWRtaW4iXX0sImV4cCI6MTU5NDczOTEwMy4zNzF9.q_0waB6B3B-0rmakxnXx202yJWbCEjvV7ntxd12UbCMG_Rra3RvwfQ7ZnNIfDIoGnqoQavqomjZNciPztyFGHA'
        }
        body = {
            "data": "86f01401-5210-4ebb-9d5e-50f9be1e149f",
            "taskId": 4
        }

        r = requests.post(domain, json=body, headers=headers, cookies=cookies)
        result = r.json()

        query = DeleteUser.objects.filter(id_response=result.get('id'), prod_type=DeleteUser.REMOVAL_REQUEST)
        if not query.exists():
            arc_user = ArcUser.objects.get(uuid=result.get('data'))
            delete_user = DeleteUser(
                id_response=result.get('id'),
                prod_type=DeleteUser.REMOVAL_REQUEST,
                status=result.get('status'),
                data=result.get('data'),
                arc_user=arc_user
            )
            delete_user.save()

    def approve_request(self):

        domain = 'https://sandbox.elcomercio.arcpublishing.com/identity/private/v1/task/approve/356'
        headers = {
            "accept": "application/json",
            "accept-language": "es-ES,es;q=0.9,en;q=0.8",
            "arc-site": "elcomercio",
            "content-type": "application/json",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        }
        cookies = {
            'Arc-Token': 'eyJpYXQiOjE1OTQ2NTI3MDMuMzcxLCJpc3MiOiJTQU1MMi9lbGNvbWVyY2lvIiwic3ViIjp7ImUiOiJqbWFjaGljYWRvQHJtZ3BlcnVzdGFmZi5jb20iLCJkIjoiSmF2aWVyIE1hY2hpY2FkbyIsImciOlsiREVWIEFkbWluIiwiRXZlcnlvbmUiLCJERVYgU1VTQyIsIlNVU0MgQWRtaW4iXX0sImV4cCI6MTU5NDczOTEwMy4zNzF9.q_0waB6B3B-0rmakxnXx202yJWbCEjvV7ntxd12UbCMG_Rra3RvwfQ7ZnNIfDIoGnqoQavqomjZNciPztyFGHA'
        }
        body = {

        }
        r = requests.put(domain, json=body, headers=headers, cookies=cookies)
        result = r.json()

        query = DeleteUser.objects.filter(id_response=result.get('id'), prod_type=DeleteUser.APPROVED_REMOVAL)
        if not query.exists():
            arc_user = ArcUser.objects.get(uuid=result.get('data'))
            delete_user = DeleteUser(
                id_response=result.get('id'),
                prod_type=DeleteUser.APPROVED_REMOVAL,
                status=result.get('status'),
                data=result.get('data'),
                arc_user=arc_user
            )
            delete_user.save()
"""
