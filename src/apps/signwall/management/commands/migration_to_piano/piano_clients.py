from urllib.parse import urljoin

from django.conf import settings
from sentry_sdk import capture_exception
import requests


class ClientBase(object):

    def api_request(self, url, method, *arg, **kwarks):
        try:
            response = getattr(requests, method)(url, *arg, **kwarks)
            data = response.json()
        except Exception:
            capture_exception()
        else:
            if response.status_code == 200:
                return data
            else:
                return {"error": response.status_code}


class PianoClient(ClientBase):
    def __init__(self):
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }

    def custom_create(self, uid, term_id, access_end_date, unlimited_access):
        url = urljoin(
            settings.PIANO_DOMAIN,
            '/api/v3/publisher/conversion/custom/create',
        )
        data = {
            "aid": 'uqsWkaVNsu',
            "api_token": settings.PAYWALL_ARC_TOKEN,
            "access_period": '',
            "term_id": term_id,
            "uid": uid,
            "extend_existing": False,
            "unlimited_access": unlimited_access
        }
        return self.api_request(url=url, headers=self.headers, json=data,
                                method='post')













