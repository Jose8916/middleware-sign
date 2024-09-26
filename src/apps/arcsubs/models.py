from datetime import date, datetime, timedelta
from urllib.parse import urljoin
import json

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.utils.crypto import get_random_string
from sentry_sdk import capture_event
from sentry_sdk import capture_exception
import pytz
import requests

from ..webutils.models import _BasicAuditedModel
from .arcclient import ArcClientAPI, IdentityClient
from .constants import SITE_CHOICES
from .utils import timestamp_to_datetime


class ArcUserManager(models.Manager):

    def get_by_uuid(self, uuid, data=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not uuid:
            raise ValueError('Users must have an UUID')

        try:
            user = self.get_queryset().get(uuid=uuid)

        except ObjectDoesNotExist:
            profile = self.get_profile(uuid=uuid, data=data)
            identities = profile.get('identities') if profile else None
            user = self.model(
                uuid=uuid,
                profile=profile,
                identities=identities
            )
            user.save(using=self._db)

        else:
            if data or not user.profile:
                user.profile = self.get_profile(uuid=uuid, data=data)
                if user.profile:
                    user.identities = user.profile.get('identities')
                user.save(using=self._db)

        return user

    def get_profile(self, uuid, data=None):
        return data if data else IdentityClient().get_user_by_uuid(uuid)


class ArcUser(_BasicAuditedModel):
    uuid = models.UUIDField(
        blank=True,
        null=True,
        unique=True
    )
    display_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='Display Name'
    )
    email = models.EmailField(
        null=True,
        blank=True
    )
    event_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Event Type'
    )
    profile = JSONField(
        null=True,
        blank=True,
        verbose_name='Profile',
    )
    identities = JSONField(
        null=True,
        blank=True,
        verbose_name='identities',
    )
    arc_state = models.NullBooleanField(
        null=True,
        blank=True
    )
    first_site = models.CharField(
        max_length=45,
        blank=True,
        null=True,
        verbose_name='Primer Portal'
    )
    last_site = models.CharField(
        max_length=35,
        blank=True,
        null=True,
        verbose_name='Último portal'
    )
    # REPORTS
    first_login_identities = JSONField(
        null=True,
        blank=True,
        verbose_name='Primer identities con login',
    )
    first_profile = JSONField(
        null=True,
        blank=True,
        verbose_name='First profile',
    )
    domain = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        verbose_name='Domain'
    )
    from_mpp = models.NullBooleanField(
        blank=True,
        null=True,
        verbose_name='Migrado de MPP'
    )
    created_on = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de registro en ARC',
        db_index=True
    )
    first_login = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Primer login'
    )
    first_login_device = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Dispositivo de login'
    )
    first_login_method = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        verbose_name='Método de login'
    )
    first_login_action = models.CharField(
        max_length=35,
        blank=True,
        null=True,
        verbose_name='Acción para login'
    )
    term_cond_pol_priv = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Terminos y Condiciones y Politicas de Privacidad'
    )
    with_activity = models.NullBooleanField(
        null=True,
        blank=True,
        verbose_name='Con actividad',
        default=False
    )
    with_subscription = models.NullBooleanField(
        null=True,
        blank=True,
        verbose_name='Con Suscripcion',
        default=False
    )
    email_verified = models.NullBooleanField(
        null=True,
        blank=True,
        verbose_name='Email verificado',
        default=False
    )
    date_verified = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de Verificacion de Email',
        db_index=True
    )
    last_login = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de ultimo login'
    )

    objects = ArcUserManager()

    class Meta:
        verbose_name = 'Usuario de ARC'
        verbose_name_plural = '[ARC] Usuarios'
        ordering = ('-created_on', '-created', )

    def save(self, *args, **kwargs):
        try:
            if not self.profile:
                self.download_data()

            self.load_data()
        except Exception:
            capture_exception()

        super().save(*args, **kwargs)

    def get_attribute(self, name, mode=None):
        if self.profile and self.profile.get('attributes'):

            for atribute in self.profile['attributes']:
                if atribute['name'] == name:
                    value = atribute['value']
                    if mode and hasattr(value, mode):
                        return getattr(atribute['value'], mode)()
                    else:
                        return value

    def get_origin_device(self, mode=None):
        value = self.get_attribute(name='originDevice', mode=mode)

        if not value and self.domain and 'pwa' in self.domain:
            value = 'Movil'

        return value

    def get_origin_action(self, mode=None):
        return self.get_attribute(name='originAction', mode=mode)

    def get_origin_action_display(self, mode=None):
        action = self.get_origin_action('lower')

        if action in ('relogin', 'openrelogin', "reloginhash", ):
            return 'Relogin'

        elif action == '0' or action == 'organico':
            return 'Organico'

        elif action == 'api':
            return 'API'

        elif action == '1':
            return 'Signwall'

        elif action == 'reloginemail':
            return 'Mailing'

        elif action == 'forgotpass':
            return None
        elif action == 'students':
            return 'students'

        elif action:
            capture_event(
                {
                    'message': 'APiLoginView.get_origin_action_display action "%s"' % action,
                    'extra': {
                        'profile': self.profile
                    }
                }
            )

    def get_origin_method(self):
        identities = self.identities or self.first_login_identities

        if identities:
            for identity in identities:
                if identity.get('type'):
                    return identity.get('type')

    def download_data(self):
        data = IdentityClient().get_user_by_uuid(self.uuid)

        if data:
            self.profile = data
            self.identities = data.get('identities')

    def load_data(self):
        if not self.profile:
            return

        identities = self.identities or self.first_login_identities or ()

        if not self.first_profile:
            self.first_profile = self.profile

        if identities and (
            not self.first_login or
            not self.first_login_identities or
            not self.first_login_method
        ):

            for identity in identities:

                first_login_timestamp = identity.get('lastLoginDate')

                if first_login_timestamp:
                    self.first_login = timestamp_to_datetime(first_login_timestamp)
                    self.first_login_identities = identities
                    self.first_login_method = identity.get('type')
                    self.first_login_device = self.get_origin_device('title')
                    self.first_login_action = self.get_origin_action_display()
                    break

        if not self.created_on and self.profile.get('createdOn'):
            self.created_on = timestamp_to_datetime(self.profile['createdOn'])

        """
        if not self.created_on:
            for identiry in identities:
                if not self.created_on and identiry.get('createdOn'):
                    self.created_on = timestamp_to_datetime(identiry['createdOn'])
                    break
        """

    def load_first_login(self, commit=True):
        """
            Registra el primer login
        """
        self.load_data()

        if commit:
            self.save()

    def localize_date(self, report_date):
        _date = datetime.strptime(report_date, "%Y-%m-%d %H:%M:%S")
        return pytz.utc.localize(_date)

    def load_report(self, report, site=None):

        if 'createdOn' in report:
            self.created_on = self.localize_date(report['createdOn'])

        # last_modified = None
        # if 'lastModifiedDate' in report:
        #     last_modified = self.localize_date(report['lastModifiedDate'])

        if not self.first_login and 'lastLoginDate' in report:
            self.first_login = self.localize_date(report['lastLoginDate'])

            if not self.first_login_method:
                self.first_login_method = self.get_origin_method()

        if site:
            if not self.first_site:
                self.first_site = site

            if not self.last_site:
                self.last_site = site

        self.save()

    def update_arc_profile(self, commit=True):
        """
            Descarga el perfil de ARC
        """
        client = ArcClientAPI()

        data = client.get_profile_by_uuid(self.uuid)

        if data:
            self.profile = data
            self.identities = data.get('identities')

        if commit:
            self.save()


class ArcUserExtraFields(_BasicAuditedModel):
    arc_user = models.ForeignKey(
        ArcUser,
        null=True,
        verbose_name='Usuario',
        related_name='user_extrafields',
        on_delete=models.PROTECT,
    )
    data_treatment = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        verbose_name='Autorización de datos'
    )

    class Meta:
        verbose_name = 'Campos extra'
        verbose_name_plural = 'Campos extra'


class Promotion(_BasicAuditedModel):
    name = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name='Nombre'
    )

    class Meta:
        verbose_name = 'Promocion'
        verbose_name_plural = '[ARC] Promociones'


class TokenUser(_BasicAuditedModel):
    token = models.TextField(
        blank=True,
        null=True,
        verbose_name='token'
    )


class RequestDeleteUser(_BasicAuditedModel):
    arc_user = models.ForeignKey(
        ArcUser,
        null=True,
        verbose_name='Usuario',
        related_name='requestdeletes',
        on_delete=models.PROTECT,
    )

    data = JSONField(
        null=True,
        blank=True,
        verbose_name='Data',
    )
    id_response = models.IntegerField(
        'Id Respuesta',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        verbose_name='estado'
    )
    log = models.TextField(
        blank=True,
        null=True,
        verbose_name='log'
    )

    class Meta:
        verbose_name = 'Solicitud de Eliminacion'
        verbose_name_plural = 'Solicitudes de Eliminacion'


class DeletedUser(_BasicAuditedModel):
    arc_user = models.ForeignKey(
        ArcUser,
        null=True,
        verbose_name='Usuario',
        related_name='deletedusers',
        on_delete=models.PROTECT,
    )

    data = JSONField(
        null=True,
        blank=True,
        verbose_name='Data',
    )
    id_response = models.IntegerField(
        'Id Respuesta',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        verbose_name='estado'
    )
    log = models.TextField(
        blank=True,
        null=True,
        verbose_name='log request'
    )

    class Meta:
        verbose_name = 'Usuario Eliminado'
        verbose_name_plural = 'Usuarios Eliminados'


class PromotionUser(_BasicAuditedModel):
    EXISTS = 1
    NEW_USER = 2

    arc_user = models.ForeignKey(
        ArcUser,
        null=True,
        related_name='user_promotion',
        verbose_name='Usuario',
        on_delete=models.PROTECT,
    )
    promotion = models.ForeignKey(
        Promotion,
        null=True,
        verbose_name='Promocion',
        on_delete=models.PROTECT,
    )
    profile = JSONField(
        null=True,
        blank=True,
        verbose_name='Profile',
    )
    state = models.IntegerField(
        'state user',
        null=True,
        blank=True
    )
    uuid = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name='UUID'
    )

    class Meta:
        verbose_name = 'Promocion del usuario'
        verbose_name_plural = '[ARC] Promociones del usuario'


class PassArcUser(_BasicAuditedModel):
    uuid = models.UUIDField(
        blank=True,
        null=True,
        unique=True
    )
    pass_encript = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Password'
    )

    class Meta:
        verbose_name = 'Pass Usuario de ARC'
        verbose_name_plural = 'Pass Usuarios de ARC'


class Report(models.Model):
    REPORT_TYPE_SIGN_UP = 'sign-up-summary'
    REPORT_TYPE_CHOICES = (
        (REPORT_TYPE_SIGN_UP, 'Registros'),
    )
    DATA_LOADED_CHOICES = (
        (None, 'Pendiente'),
        (True, 'Completa'),
        (False, 'Incompleta'),
    )
    start_date = models.DateTimeField(
        'Fecha de inicio',
        null=True
    )
    end_date = models.DateTimeField(
        'Fecha de fin',
        null=True,
        blank=True
    )
    report_type = models.CharField(
        'Tipo',
        max_length=50,
        null=True,
        choices=REPORT_TYPE_CHOICES,
        default=REPORT_TYPE_SIGN_UP
    )
    site = models.CharField(
        'Portal',
        max_length=20,
        null=True,
        choices=SITE_CHOICES
    )
    payload = JSONField(
        'Request',
        null=True,
        blank=True
    )
    result = JSONField(
        'Responce',
        null=True,
        blank=True
    )
    error = JSONField(
        'Error',
        null=True,
        blank=True
    )
    data = models.FileField(
        'Reporte',
        null=True,
        blank=True
    )
    records = models.IntegerField(
        'Número de registros',
        null=True,
        blank=True
    )
    hits = models.IntegerField(
        'Número de intentos',
        null=True,
        blank=True,
        default=0
    )
    data_loaded = models.NullBooleanField(
        'Carga de datos',
        null=True,
        blank=True,
        choices=DATA_LOADED_CHOICES
    )

    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = '[ARC] Reportes'

    def save(self, *args, **kwargs):

        if not self.end_date:
            self.end_date = datetime.combine(
                self.start_date.date(),
                datetime.max.time()
            ) + timedelta(seconds=1)

        self.request_report()
        self.download_report()
        super().save(*args, **kwargs)

        if self.data and self.records and self.data_loaded is None:
            self.load_data()
            super().save(*args, **kwargs)

    def datetime_to_javadate(self, _date):
        data = _date.utctimetuple()
        return "{}-{}-{}T{}:{}:{}.000Z".format(*data)

    def get_file_name(self):
        return 'reports/{day}/{jobid}_{hash}.json'.format(
            day=date.today(),
            jobid=self.result.get('jobID'),
            hash=get_random_string(length=8),
        )

    def download_report(self):
        jobid = self.result.get('jobID')

        if not jobid or self.records is not None or self.hits > 20:
            return

        url = urljoin(
            settings.PAYWALL_ARC_URL,
            "identity/api/v1/report/{jobid}/download".format(jobid=jobid)
        )

        headers = {
            'Content-Type': "application/json",
            'Authorization': "Bearer " + settings.PAYWALL_ARC_TOKEN,
            'Arc-Site': self.site
        }

        try:
            response = requests.request("GET", url, data="", headers=headers)
            result = response.json()

        except Exception:
            capture_exception()

        else:
            if response.status_code == 200:
                content = ContentFile(response.content)
                file_path = default_storage.save(self.get_file_name(), content)

                self.error = None
                self.data = file_path
                self.records = len(result)
            else:
                self.error = result
                self.hits += 1

    def request_report(self):

        if self.result and self.result.get('jobID'):
            return

        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + settings.PAYWALL_ARC_TOKEN,
            'Arc-Site': self.site
        }
        self.payload = {
            "name": "report",
            "startDate": self.datetime_to_javadate(self.start_date),
            "endDate": self.datetime_to_javadate(self.end_date),
            "reportType": self.report_type,
            "reportFormat": "json"
        }
        url = urljoin(settings.PAYWALL_ARC_URL, 'identity/api/v1/report/schedule')
        try:
            response = requests.post(url, json=self.payload, headers=headers)
            result = response.json()

        except Exception:
            capture_exception()

        else:
            self.result = result

    def load_data(self):

        if not self.data or not self.records or self.data_loaded is not None:
            return

        try:
            records = json.loads(self.data.read())

            for record in records:
                arc_user = ArcUser.objects.get_by_uuid(uuid=record['clientId'])
                arc_user.load_report(record, site=self.site)

        except Exception:
            capture_exception()
            self.data_loaded = False

        else:
            self.data_loaded = True


class Event(_BasicAuditedModel):
    index = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='Code',
    )
    event_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Tipo',
    )
    message = JSONField(
        null=True,
        blank=True,
        verbose_name='Message',
    )
    site = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Site',
    )
    timestamp = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='timestamp',
    )

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = '[ARC] Notificaciones'


class ArcUserReport(_BasicAuditedModel):
    uuid = models.UUIDField(
        blank=True,
        null=True,
        unique=True,
        db_index=True,
    )
    last_modified_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Ultima fecha de modificacion',
        db_index=True,
    )
    last_login_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='ultima fecha de login',
        db_index=True,
    )
    created_on = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de registro en ARC',
        db_index=True,
    )
    site = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Site',
    )
    body = JSONField(
        null=True,
        blank=True,
        verbose_name='registro',
    )
    user = models.OneToOneField(
        ArcUser,
        on_delete=models.PROTECT,
        verbose_name='Usuario',
        null=True,
        editable=False,
    )

    class Meta:
        verbose_name = '[Reporte] Usuario de ARC'
        verbose_name_plural = '[Reporte] Usuarios'
        ordering = ('-created_on', '-created', )


class LogArcUserReport(_BasicAuditedModel):
    schedule_request = JSONField(
        null=True,
        blank=True,
        verbose_name='schedule request',
    )
    schedule_response = JSONField(
        null=True,
        blank=True,
        verbose_name='schedule response',
    )
    download_total = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='Total',
    )
    site = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Site',
    )

    class Meta:
        verbose_name = '[Log] Reporte Usuario de ARC'
        verbose_name_plural = '[Log] Reporte Usuarios'
        ordering = ('created', )
