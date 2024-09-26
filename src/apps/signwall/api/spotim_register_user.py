# -*- coding: utf-8 -*-

import json
import requests
from django.http import JsonResponse, HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.webutils.utils import normalize_text
from apps.signwall.utils import search_user_arc_param
from apps.signwall.utils import get_profile_user_arc


class SpotimRegisterUserApiView(APIView):
    permission_classes = (AllowAny,)

    def get_display_name(self, received_json_data):
        try:
            value = received_json_data.get('user_name', '')
            if value:
                return normalize_text(value)
        except Exception as e:
            print(e)
            print('no existe user_name')
            return ''

    def get_code_a(self, received_json_data):
        try:
            value = received_json_data.get('code_a', '')
            if value:
                return value.strip()
        except Exception as e:
            print(e)
            print('no envio code_a')
            return ''

    def get_user_email(self, received_json_data):
        try:
            value = received_json_data.get('user_email', '')
            if value:
                return normalize_text(value)
        except Exception as e:
            print(e)
            print('no existe user_email')
            return ''

    def get_uuid(self, received_json_data):
        try:
            value = received_json_data.get('uuid', '')
            if value:
                return normalize_text(value)
        except Exception as e:
            print(e)
            print('no existe user_ecoid')
            return ''

    def get_avatar(self, received_json_data):
        try:
            value = received_json_data.get('avatar', '')
            print(value)
            if value:
                return value.strip()
            else:
                return ''
        except Exception as e:
            print(e)
            print('no existe avatar')
            return ''

    def get_verified_user(self, uuid):
        try:
            user = search_user_arc_param('uuid', uuid)
            if user.get('totalCount', ''):
                result = user.get('result', '')[0]
                return result.get('profile').get('emailVerified')
            else:
                return 'false'
        except Exception as e:
            print(e)
            return 'false'

    def get_unique_user_name(self, received_json_data):
        # unique user name
        try:
            value = received_json_data.get('unique_user_name', '')
            if value:
                first_word = value.strip().split(' ')
                return first_word[0]
        except Exception as e:
            print(e)
            print('no existe user_name')
            return ''

    def post(self, request, *args, **kwargs):
        data_response = {
            "httpStatus": 400,
            "message": "No se formulo bien la peticion"
        }

        if request.headers['token']:
            profile_user = get_profile_user_arc(request.headers['token'], request.headers['site'])
            if profile_user.get('httpStatus'):
                data_response = {
                    "httpStatus": profile_user.get('httpStatus'),
                    "message": "Token incorrecto"
                }
                return JsonResponse(data_response)
        else:
            return JsonResponse(data_response)
        DOMAIN_SPOTIM = 'https://www.spot.im'
        ACCESS_TOKEN = '03180307nMqKgn'
        body = request.body.decode('utf-8')
        received_json_data = json.loads(body)

        code_a = self.get_code_a(received_json_data)
        user_name = self.get_user_email(received_json_data) # unique user name
        display_name = self.get_display_name(received_json_data)  # full name
        user_email = self.get_user_email(received_json_data)
        uuid = self.get_uuid(received_json_data)
        verify = self.get_verified_user(uuid)
        avatar = self.get_avatar(received_json_data)

        if code_a and user_name and user_email and uuid:
            url_path = "/api/sso/v1/register-user?code_a={}&access_token={}&primary_key={}&user_name={}" \
                       "&display_name={}&image_url={}&email={}&verified={}".format(
                            code_a,
                            ACCESS_TOKEN,
                            uuid,
                            user_name,
                            display_name,
                            avatar,
                            user_email,
                            verify
                       )

            try:
                response = requests.get(str(DOMAIN_SPOTIM) + str(url_path))
                data_response = {
                    "code": response.text
                }
                return JsonResponse(data_response)
            except Exception as e:
                print(e)
                data_response = {
                    "httpStatus": "400",
                    "message": "No se formulo bien la peticion"
                }
                return JsonResponse(data_response)
        else:
            return JsonResponse(data_response)
