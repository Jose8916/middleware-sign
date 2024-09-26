import json

from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.signwall.models import PassArcUser
from apps.arcsubs.models import PromotionUser, Promotion, ArcUser
from apps.signwall.utils import random_characters, create_user_arc, search_user_arc
from apps.webutils.utils import normalize_text, validar_email, characters_special
from apps.arcsubs.constants import TOKENS

from sentry_sdk import capture_exception, capture_event, capture_message


class UserArcApiView(APIView):
    permission_classes = (AllowAny,)

    def get_first_name(self, received_json_data):
        value = received_json_data.get('first_name', '')
        return normalize_text(value, 'title')

    def get_last_name_male(self, received_json_data):
        value = received_json_data.get('apellido_paterno', '')
        return normalize_text(value, 'title')

    def get_last_name_female(self, received_json_data):
        value = received_json_data.get('apellido_materno', '')
        return normalize_text(value, 'title')

    def get_referer(self, received_json_data):
        try:
            value = received_json_data.get('referer', '').strip()
            return value
        except:
            return ''

    def get_extra_fields(self, received_json_data):
        try:
            value = received_json_data.get('extra_fields', '')

            return value
        except:
            return ''

    def get_gender(self, received_json_data):
        try:
            value = received_json_data.get('gender', '')

            return value
        except:
            return ''

    def get_birth_year(self, received_json_data):
        try:
            value = received_json_data.get('birth_year', '')
            return value
        except:
            return ''

    def get_birth_month(self, received_json_data):
        try:
            value = received_json_data.get('birth_month', '')
            return value
        except:
            return ''

    def get_birth_day(self, received_json_data):
        try:
            value = received_json_data.get('birth_day', '')
            return value
        except:
            return ''

    def get_cellphone(self, received_json_data):
        try:
            value = received_json_data.get('cellphone', '')
            return value
        except:
            return ''

    def get_promociones(self, received_json_data):
        try:
            value = received_json_data.get('promociones', '')
            return value
        except:
            return ''

    def get_domain(self, received_json_data):
        try:
            value = received_json_data.get('domain', '')
            return value
        except:
            return ''

    def get_email(self, received_json_data):
        try:
            value = received_json_data.get('email', '')
            value = normalize_text(value, 'lower')
            if not validar_email(value):
                return ''
            is_valid = characters_special(value)
            if is_valid:
                return value
            else:
                return ''
        except:
            return ''

    def save_promotion_user(self, uuid, promociones, received_json_data, state):
        obj_promotion, created = Promotion.objects.get_or_create(name=promociones)
        try:
            promotion_user_uuid = PromotionUser.objects.filter(uuid=uuid, promotion=obj_promotion).exists()
        except Exception:
            promotion_user_uuid = ''

        if not promotion_user_uuid:
            try:
                if state == PromotionUser.EXISTS:
                    arc_user = ArcUser.objects.get(uuid=uuid)
                else:
                    arc_user = ''
            except Exception:
                arc_user = ''

            try:
                promotion_user_arc_user = PromotionUser.objects.filter(arc_user=arc_user, promotion=obj_promotion).exists()
            except Exception:
                promotion_user_arc_user = ''

            if not promotion_user_arc_user and not promotion_user_uuid:
                if arc_user:
                    promotion_user = PromotionUser(
                        arc_user=arc_user,
                        promotion=obj_promotion,
                        profile=received_json_data,
                        state=state,
                        uuid=uuid
                    )
                    promotion_user.save()
                else:
                    promotion_user = PromotionUser(
                        promotion=obj_promotion,
                        profile=received_json_data,
                        state=state,
                        uuid=uuid
                    )
                    promotion_user.save()

    def post(self, request, *args, **kwargs):
        data_response = {}
        if 'H3DBIESB7CEF112308NKI2JLBP7LJA5uZhsfTw7hasCJWov+5XyT/UnDZW87JtPWJXaX9tM' in request.headers['Authorization']:
            body = request.body.decode('utf-8')
            received_json_data = json.loads(body)

            email = self.get_email(received_json_data)
            if not email:
                data_response = {
                    'estado': 'datos incorrectos'
                }
            else:
                domain = self.get_domain(received_json_data)

                first_name = self.get_first_name(received_json_data)
                apellido_paterno = self.get_last_name_male(received_json_data)
                apellido_materno = self.get_last_name_female(received_json_data)
                extra_fields = self.get_extra_fields(received_json_data)
                gender = self.get_gender(received_json_data)
                birth_year = self.get_birth_year(received_json_data)
                birth_month = self.get_birth_month(received_json_data)
                birth_day = self.get_birth_day(received_json_data)
                cellphone = self.get_cellphone(received_json_data)
                promociones = self.get_promociones(received_json_data)

                result = search_user_arc(email)
                if result.get('totalCount', ''):
                    existe = result.get('result')[0]
                    if promociones:
                        self.save_promotion_user(existe.get('uuid'), promociones, received_json_data, PromotionUser.EXISTS)
                    data_response = {
                        'uuid': existe.get('uuid'),
                        'tipo': 'existe'
                    }
                elif not domain:
                    data_response = {
                        'estado': 'dominio incorrecto'
                    }
                else:
                    arc_profile = {}
                    arc_profile['email'] = email
                    arc_profile['displayName'] = email
                    if first_name:
                        arc_profile['firstName'] = first_name

                    if apellido_paterno:
                        arc_profile['lastName'] = apellido_paterno

                    if apellido_materno:
                        arc_profile['secondLastName'] = apellido_materno

                    if gender:
                        arc_profile['gender'] = gender

                    if birth_year:
                        arc_profile['birthYear'] = birth_year

                    if birth_month:
                        arc_profile['birthMonth'] = birth_month

                    if birth_day:
                        arc_profile['birthDay'] = birth_day

                    if cellphone:
                        arc_profile['contacts'] = [
                            {
                                "phone": cellphone,
                                "type": "PRIMARY"
                            }
                        ]

                    pass_user = random_characters(8)

                    if self.get_referer(received_json_data):
                        referer = self.get_referer(received_json_data)
                    else:
                        referer = domain

                    result = create_user_arc(email, arc_profile, pass_user, domain, referer, extra_fields, promociones)

                    user_pass = PassArcUser(uuid=result.get('uuid'), pass_encript=pass_user)
                    user_pass.save()
                    data_response = {
                        'uuid': result.get('uuid'),
                        'tipo': 'registrado',
                        'claveuser': pass_user
                    }

                    if 'uuid' not in result:
                        data_response['error'] = result
                    else:
                        if promociones:
                            self.save_promotion_user(result.get('uuid'), promociones, received_json_data, PromotionUser.NEW_USER)

        else:
            data_response = {
                'estado': 'No formulo bien la peticion'
            }

        return JsonResponse(data_response)
