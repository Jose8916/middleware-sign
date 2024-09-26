from datetime import datetime, timedelta
from urllib.parse import urljoin
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone
from sentry_sdk import capture_message
import requests

from apps.arcsubs.models import ArcUser, ArcUserReport, LogArcUserReport
from apps.signwall.utils import search_user_arc_param
from apps.signwall.models import UsersReport
from apps.signwall.utils import utc_to_lima_time_zone


class Command(BaseCommand):
    help = 'Load users  from ARC, que no llegaron por los eventos'
    # python3 manage.py load_users_arc

    def load_user(self, user_data, site):
        result = user_data.get('result', '')[0]
        user_data = result.get('profile', '')
        uuid = result.get('uuid', '')

        headers = {
            'content-type': 'application/json'
        }

        payload = {
            "eventTime": user_data['createdOn'],
            "index": user_data['createdOn'],
            "message":
                {
                    "email": user_data['email'],
                    "identifier": user_data['email'],
                    "uuid": uuid
                },
            "site": str(site),
            "type": 'USER_SIGN_UP'
        }

        url = settings.EVENTS_LAMBDA + str('/v1/service/arc/events')

        try:
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()

            return result
        except Exception:
            print('Error en lambda')
            return ""

    def handle(self, *args, **options):
        users = ArcUserReport.objects.filter(
            user=None
        )
        for user in users:
            if ArcUser.objects.filter(uuid=user.uuid).exists():
                user.user = ArcUser.objects.get(uuid=user.uuid)
                user.save()
                print('guardado')
            else:
                user_data = search_user_arc_param('uuid', user.uuid)
                if user_data.get('totalCount', ''):
                    respuesta = self.load_user(user_data, user.site)
                    print(user.uuid)
                    print(respuesta)

