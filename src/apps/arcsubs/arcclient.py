from urllib.parse import urljoin

from django.conf import settings
from sentry_sdk import capture_exception, capture_event, capture_message
import requests
import json

# import curlify


class ArcClientAPI(object):
    """Cliente de ARC que permite operaciones internas"""

    def __init__(self):
        self.headers = {"Authorization": "Bearer %s" %
                        settings.PAYWALL_ARC_TOKEN}

    def get_profile_by_uuid(self, uuid):

        url = urljoin(settings.PAYWALL_ARC_URL,
                      "/identity/api/v1/profile/%s" % uuid)

        try:
            response = requests.get(url, headers=self.headers)
            result = response.json()

        except Exception:
            # capture_exception()
            pass

        else:
            if response.status_code != 200:
                capture_event(
                    {
                        "message": "ArcClientAPI.get_profile_by_uuid error",
                        "extra": {"uuid": uuid, "url": url, "response": result},
                    }
                )
            else:
                return result

    def update_DisplayName_in_Profile_by_uuid(
        self,
        uuid: str,
        new_displayName: str,
        verbose: bool = False,
        safe=False  # Safe mean PATCH instead of PUT
    ):
        """Actualiza el Profile de ARC con el uuid del usuario

        Args:
            - uudi (str) : uuid del usuario de ARC
            - new_displayName (str): string to replace the old one. *Default: user's email or null.
            - safe (bool): Safe enable is PATCH, else is PUT
        Returns:
            - response (requests.Response()): server response

        Example with CURL:

        ```bash
        curl --location --request \
            PUT 'https://api.sandbox.elcomercio.arcpublishing.com/identity/api/v1/profile/<<uuid>>' \
            --header 'Content-Type: application/json' \
            --header 'Authorization: Bearer token' \
            --data-raw '{
                "firstName": "Juan Pedro",
                [... ] # continua
                }'
        ```

        Documentation ARC and error codes:
        - https://elcomercio.arcpublishing.com/alc/docs/swagger/
        ?url=./arc-products/arc-identity-v1-api.json#/User_Registration/updateProfile
        """
        current_file = __file__.rsplit("/", 1)[1].split(".")[0]

        if not new_displayName:
            print(f"[ERROR] Valor de new_displayName: {new_displayName}")
            raise (ValueError)

        url = urljoin(settings.PAYWALL_ARC_URL,
                      "/identity/api/v1/profile/%s" % uuid)

        if safe == False:

            result_json = self.get_profile_by_uuid(uuid)
            if verbose:
                print(f"[{current_file}] OLD result_json=",
                      json.dumps(result_json), "\n")
            result_json["displayName"] = new_displayName
            if verbose:
                print(
                    f"[{current_file}] MODIFIED result_json=", json.dumps(
                        result_json), "\n"
                )

            # PUT
            try:
                response = requests.put(
                    url, headers=self.headers, json=result_json)
                # if verbose:
                #     print(curlify.to_curl(response.request))
                if response.status_code == 200:
                    new_result_json = self.get_profile_by_uuid(uuid)
                    if verbose:
                        print(
                            f"[{current_file}] NEW result_json=",
                            json.dumps(new_result_json),
                            "\n",
                        )
                else:
                    print(
                        f"[ERROR][{current_file}] {response} {response.json()}")
                    raise ConnectionError()
            except Exception:
                capture_exception()

            else:
                if response.status_code != 200:
                    capture_event(
                        {
                            "message": "ArcClientAPI.update_DisplayName_in_Profile_by_uuid error",
                            "extra": {"uuid": uuid, "url": url, "response": response},
                        }
                    )
                else:
                    return response
        elif safe == True:

            result_json = {}
            if verbose:
                print(f"[{current_file}] OLD result_json=",
                      json.dumps(result_json), "\n")
            result_json["displayName"] = new_displayName
            if verbose:
                print(
                    f"[{current_file}] MODIFIED result_json=", json.dumps(
                        result_json), "\n"
                )

            # PATCH
            try:
                response = requests.patch(
                    url, headers=self.headers, json=result_json)
                # if verbose:
                #     print(curlify.to_curl(response.request))
                if response.status_code == 200:
                    new_result_json = self.get_profile_by_uuid(uuid)
                    if verbose:
                        print(
                            f"[{current_file}] NEW result_json=",
                            json.dumps(new_result_json),
                            "\n",
                        )
                else:
                    print(
                        f"[ERROR][{current_file}] {response} {response.json()}")
                    raise ConnectionError()
            except Exception:
                capture_exception()

            else:
                if response.status_code != 200:
                    capture_event(
                        {
                            "message": "ArcClientAPI.update_DisplayName_in_Profile_by_uuid error",
                            "extra": {"uuid": uuid, "url": url, "response": response},
                        }
                    )
                else:
                    return response
        
    def create_report(self, date_i, date_e):
        payload = {
            "name": "report_user",
            "startDate": date_i,
            "endDate": date_e,
            # "reportType": "sign-up-summary",
            "reportType": "sign-up-summary",
            "reportFormat": "json"}

        url = urljoin(settings.PAYWALL_ARC_URL,
                      "/identity/api/v1/report/schedule")
        print(payload)
        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(payload))
            if response.status_code == 200:
                return response.json().get("jobID")
            else:
                print(response.json())
        except Exception as e:
            raise e

    def create_sale_report(self, date_i, date_e):
        payload = {
            "name": "report_user",
            "startDate": date_i,
            "endDate": date_e,
            "reportType": "subscription-event",
            "reportFormat": "json"}
        print(payload)
        url = urljoin(settings.PAYWALL_ARC_URL,
                      "/sales/api/v1/report/schedule")
        try:
            response = requests.post(url, headers=self.headers,
                                     data=json.dumps(payload))
            if response.status_code == 200:
                return response.json().get("jobID")
            else:
                print(response.json())
        except Exception as e:
            print(response.json())
            raise e

    def download_report(self, job_id):
        pre_url = f"/identity/api/v1/report/{job_id.strip()}/download"
        url = urljoin(settings.PAYWALL_ARC_URL, pre_url)
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(response.json())
                raise Exception
        except Exception as e:
            raise e

    def download_sale_report(self, job_id):
        pre_url = f"/sales/api/v1/report/{job_id.strip()}/download"
        url = urljoin(settings.PAYWALL_ARC_URL, pre_url)
        print(self.headers)
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(response)
                raise Exception
        except Exception as e:
            raise e

    def get_subscription(self, subscription_id):
        pre_url = f'/sales/api/v1/subscription/{subscription_id}/details'
        url = urljoin(settings.PAYWALL_ARC_URL, pre_url)
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(response)
                raise Exception
        except Exception as e:
            raise e


class IdentityClient(object):
    def get_user(self, identify):
        if "@" in identify:
            raise Exception("get_user_by_email error")
        else:
            return self.get_user_by_uuid(identify)

    def get_user_by_uuid(self, uuid):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + settings.PAYWALL_ARC_TOKEN,
        }
        url = settings.PAYWALL_ARC_URL + "/identity/api/v1/profile/{uuid}".format(
            uuid=uuid
        )
        try:
            response = requests.get(url, headers=headers)
            data = response.json()

        except Exception:
            capture_exception()

        else:
            if response.status_code == 200:
                return data

            else:
                capture_message(response.text)

    def get_subscriptions_by_user(self, site, uid):

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + settings.PAYWALL_ARC_TOKEN
        }

        url = '{dominio}/sales/api/v1/subscription/all?id={uid}&site={brand}'.format(
            dominio=settings.PAYWALL_ARC_URL,
            uid=uid,
            brand=site
        )

        try:
            response = requests.get(url, headers=headers)
            data = response.json()

        except Exception:
            capture_exception()

        else:
            if response.status_code == 200:
                return data

            else:
                capture_message(response.text)