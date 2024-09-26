from datetime import datetime, date, timedelta

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.utils.timezone import get_default_timezone
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from sentry_sdk import capture_event, capture_exception

from apps.arcsubs.models import ArcUser
from apps.signwall.utils import generate_dmp_hash_v2


site_key_dic = {
    "elcomercio": "7",  # elcomercio
    "gestion": "1",  # gestion
    "elbocon": "11",  # elbocon
    "trome": "4",  # trome
    "depor": "6",  # depor
    "diariocorreo": "12",  # diariocorreo
    "peru21": "2",  # peru21
    "suscripciones.elcomercio.pe": "9",  # suscripciones.elcomercio.pe
    "suscripciones.gestion.pe": "16"  # suscripciones.gestion.pe
}


class ARCToDwhByUUIApiView(APIView):
    permission_classes = (AllowAny,)

    SUSCRIPCIONES_NAME = ['suscripciones.elcomercio.pe', 'suscripciones.gestion.pe']

    def site_key(self, user):
        return site_key_dic.get(user.first_site, '')

    def get_domain_excluded(self, site_name):
        for domain in self.SUSCRIPCIONES_NAME:
            if site_name in domain:

                if settings.ENVIRONMENT != 'production':
                    domain = 'pre.{}'.format(domain)

                return domain

    def get(self, request, *args, **kwargs):
        uuid = request.GET.get('uuid', '')

        try:
            user = ArcUser.objects.get(uuid=uuid)
        except Exception:
            return JsonResponse([], safe=False)

        try:
            profile = self.format_user(user)
            return JsonResponse(profile, safe=False)
        except Exception:
            capture_exception()
            return JsonResponse([], safe=False)

    def update_datetime(self, update_datetime_timestamp):
        if update_datetime_timestamp:
            dt_object = datetime.fromtimestamp(update_datetime_timestamp / 1000.0)
            return dt_object
        else:
            return "1900-01-01T00:00:00"

    def register_date(self, register_date):
        return datetime.fromtimestamp(register_date / 1000.0)

    def last_login_date(self, identities):
        lista_last_login = []
        last_login_uTimestamp = ''
        if identities:
            if len(identities):
                for identity in identities:
                    if identity.get('lastLoginDate', ''):
                        lista_last_login.append(identity.get('lastLoginDate', ''))
                if lista_last_login and lista_last_login != [None]:
                    last_login_uTimestamp = max(lista_last_login)
                else:
                    last_login_uTimestamp = ''

        if last_login_uTimestamp:
            dt_object = datetime.fromtimestamp(last_login_uTimestamp / 1000.0)
        else:
            dt_object = ''
        return dt_object

    def birth_date(self, user):
        if user.get('birthYear') and user.get('birthMonth') and user.get('birthDay'):
            birth_date = date(int(user.get('birthYear')), int(user.get('birthMonth')), int(user.get('birthDay')))
            return birth_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            return "1900-01-01T00:00:00"

    def dni(self, user_attrib):
        if user_attrib:
            if len(user_attrib):
                for user_obj in user_attrib:
                    if user_obj.get('name', '') == 'documentNumber':
                        return user_obj.get('value', '')
        return ""

    def country(self, user_attrib):
        if user_attrib:
            if len(user_attrib):
                for user_obj in user_attrib:
                    if user_obj.get('name', '') == 'country':
                        return user_obj.get('value', '')
        return ""

    def phone(self, user_attrib):
        if user_attrib:
            if len(user_attrib):
                for user_obj in user_attrib:
                    if user_obj.get('name', '') == 'mobilePhone':
                        return user_obj.get('value', '')
        return ""

    def cellphone(self, user_attrib):
        if user_attrib:
            if len(user_attrib):
                for user_obj in user_attrib:
                    if user_obj.get('name', '') == 'phone':
                        return user_obj.get('value', '')
        return ""

    def device(self, user_attrib):
        if user_attrib:
            if len(user_attrib):
                for user_obj in user_attrib:
                    if user_obj.get('name', '') == 'originDevice':
                        return user_obj.get('value', '')
        return ""

    def gender(self, user_profile):
        genero = user_profile.get('gender', '')

        if genero:
            if genero == 'MALE':
                gender = 'M'
            elif genero == 'FEMALE':
                gender = 'F'
            else:
                gender = 'N'
        else:
            gender = 'N'
        return gender

    def type_access(self, user_attrib):
        if user_attrib:
            if len(user_attrib):
                for user_obj in user_attrib:
                    if user_obj.get('name', '') == 'originMethod':
                        if user_obj.get('value', '') == 'formulario':
                            return 1
                        else:
                            return user_obj.get('value', '')
        return ""

    def last_name_f(self, user_attrib):
        if user_attrib:
            if len(user_attrib):
                for user_obj in user_attrib:
                    if user_obj.get('name', '') == 'secondLastName':
                        return user_obj.get('value', '')
        return ""

    def full_last_name(self, user):
        if user:
            if self.last_name_f(user.profile.get('attributes', {})):
                if user.profile:
                    if user.profile.get('lastName', ''):
                        user.profile.get('lastName', '') + ' ' + self.last_name_f(user.profile.get('attributes', {}))
                    else:
                        return self.last_name_f(user.profile.get('attributes', {}))
                else:
                    return self.last_name_f(user.profile.get('attributes', {}))
            else:
                return "-"
        else:
            return "-"

    def user_identifier(self, id_user):
        return id_user + 601000000

    def origin_referer(self, user_attrib):
        if user_attrib:
            if len(user_attrib):
                for user_obj in user_attrib:
                    if user_obj.get('name', '') == 'originReferer':
                        if len(user_obj.get('value', '')) < 140:
                            return user_obj.get('value', '')
                        else:
                            return user_obj.get('value', '')[:140]

        return ""

    def originAction(self, user_attrib):
        if user_attrib:
            if len(user_attrib):
                for user_obj in user_attrib:
                    if user_obj.get('name', '') == 'originAction':
                        return user_obj.get('value', '')
        return ""

    def get_email(self, user):
        email = ''

        if user.email:
            email = user.email

        identities = user.identities or user.first_login_identities
        if not email and identities:
            for identity in identities:
                if identity['type'] == 'Facebook':
                    email = '{}@facebook.com'.format(identity['userName'])
                    break

        if not email:
            capture_event(
                {
                    'message': 'ARCToDwhApiView warning: Usuario sin email',
                    'extra': {'user.id': user.id},
                }
            )

        return email.strip().lower()

    def format_user(self, user):
        email = self.get_email(user)

        return {
            "action_register": self.originAction(user.profile.get('attributes', {})),
            "arc_uuid": user.uuid,
            "avatar": "",  # actualmente envia vacio
            "avatar_50": "",  # actualmente envia vacio
            "birth_date": self.birth_date(user.profile),
            "birth_year": "",  # actualmente envia vacio
            "cellphone": self.cellphone(user.profile.get('attributes', {})),
            "city": "",
            "civilstatus": user.profile.get('civilStatus', ''),
            "country": self.country(user.profile.get('attributes', {})),
            "device": self.device(user.profile.get('attributes', {})),
            "direction": "",  # actualmente envia vacio
            "dmp_hash": generate_dmp_hash_v2(email),
            "dni": self.dni(user.profile.get('attributes', {})),
            "eco_id": self.user_identifier(user.id),
            "email": email,
            "estado": "",  # investigar
            "first_name": user.profile.get('firstName', ''),
            "from_mpp": user.from_mpp,
            "gender": self.gender(user.profile),
            "high": True,
            "high_date": "1900-01-01T00:00:00",
            "id": self.user_identifier(user.id),
            "last_login": self.last_login_date(user.identities),
            "last_name": self.full_last_name(user),
            "last_name_f": self.last_name_f(user.profile.get('attributes', {})),  # apellido paterno
            "last_name_m": user.profile.get('lastName', ''),  # apellido materno
            "low": False,
            "low_date": "1900-01-01T00:00:00",
            "migration": False,  # actualmente envia False
            "migration_done": False,  # actualmente envia False
            "newsletter": True,  # Opcion por default
            "nickname": "",  # actualmente envia vacio
            "origin_referer": self.origin_referer(user.profile.get('attributes', {})),
            "phone": self.phone(user.profile.get('attributes', {})),
            "postalcode": "",  # actualmente envia vacio
            "privacy_accepted_date": "1900-01-01",
            "privacy_version": "",  # actualmente envia vacio
            "register_date": self.register_date(user.profile.get('createdOn')),
            "section": "",  # actualmente se envia vacio
            "site": self.site_key(user),
            "social_id": "",  # actualmente envia vacio
            "source": "",  # actualmente envia vacio
            "term_conditions": "",  # actualmente envia vacio
            "token_activate": "",  # actualmente envia vacio
            "tyc_accepted_date": "1900-01-01",
            "tyc_version": "",  # actualmente envia vacio
            "type": self.type_access(user.profile.get('attributes', {})),
            "update_datetime": self.update_datetime(user.profile.get('modifiedOn')),
            "update_last": "1900-01-01T00:00:00",
            "username": "-",  # actualmente se envia asi
            "version": "",  # actualmente envia vacio
        }
