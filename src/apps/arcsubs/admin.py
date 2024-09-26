import csv
import json
from datetime import datetime, timedelta
from io import StringIO

import requests
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.postgres import fields
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Q
from django.db.models.functions import TruncDay
from django.http import HttpResponse
from django.http.response import StreamingHttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.utils import formats, timezone
from django.utils.html import format_html
from django.utils.text import Truncator
from django_json_widget.widgets import JSONEditorWidget
from rangefilter.filter import DateTimeRangeFilter

from ..webutils.admin import _AuditedModelMixin
from .models import (
    ArcUser,
    Event,
    Report,
    PromotionUser,
    Promotion,
    ArcUserReport,
    LogArcUserReport,
    TokenUser,
    RequestDeleteUser,
    DeletedUser,
    ArcUserExtraFields,
)
from .utils import date_to_localtime, timestamp_to_datetime


@admin.register(Event)
class EventAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = (
        "hora_registro",
        "created",
        "timestamp",
        "message",
        "event_type",
        "site",
    )
    list_filter = (
        "site",
        "event_type",
    )
    search_fields = ("message", "event_type")

    def hora_registro(self, obj):
        return datetime.fromtimestamp(obj.timestamp / 1000.0)


@admin.register(ArcUserExtraFields)
class ArcUserExtraFieldsAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = (
        "get_display_name",
        "get_important_dates",
        "data_treatment",
    )
    list_filter = ("data_treatment", "arc_user__first_site")
    readonly_fields = ("arc_user",)

    def get_display_name(self, obj):
        return format_html(
            "{full_name}</br>"
            '<i class="fas fa-fingerprint"></i> {uuid}</br>'
            '<i class="fas fa-at"></i> {email}</br>'
            '<i class="fas fa-newspaper"></i> {site}</br>',
            full_name=self.get_fullname(obj.arc_user),
            uuid=obj.arc_user.uuid,
            email=obj.arc_user.email,
            site=obj.arc_user.first_site or "--",
        )

    def get_fullname(self, obj):
        if obj.profile:
            first_name = obj.profile.get("firstName") or ""
            last_name = obj.profile.get("lastName") or ""
            second_last_name = obj.profile.get("secondLastName") or ""
            if first_name or last_name or second_last_name:
                full_name = "{} {} {}".format(
                    first_name, last_name, second_last_name)
            else:
                full_name = ""
            return Truncator(full_name).chars(50)

    def get_queryset(self, request):
        qs = super(ArcUserExtraFieldsAdmin, self).get_queryset(request)
        return qs.order_by("-arc_user__created_on")

    def get_important_dates(self, obj):
        date_created = obj.arc_user.profile.get("createdOn")
        date_created = timestamp_to_datetime(date_created)

        modified_on = obj.arc_user.profile.get("modifiedOn")
        modified_on = timestamp_to_datetime(modified_on)

        date_verified = (
            obj.arc_user.date_verified.astimezone(
                timezone.get_current_timezone())
            if obj.arc_user.date_verified
            else None
        )

        tz_first_login = (
            obj.arc_user.first_login.astimezone(
                timezone.get_current_timezone())
            if obj.arc_user.first_login
            else None
        )

        return format_html(
            "<b>Registro:</b> {}</br>"
            "<b>Fecha de verificación:</b> {}</br>"
            "<b>Actualización:</b> {}</br>"
            "<b>Primer login:</b> {}</br>",
            formats.date_format(date_created, settings.DATETIME_FORMAT)
            if date_created
            else "--",
            formats.date_format(date_verified, settings.DATETIME_FORMAT)
            if date_verified
            else "--",
            formats.date_format(modified_on, settings.DATETIME_FORMAT)
            if modified_on
            else "--",
            formats.date_format(tz_first_login, settings.DATETIME_FORMAT)
            if tz_first_login
            else "--",
        )


@admin.register(Report)
class ReportAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = ("start_date", "end_date", "site", "records", "data_loaded")


def sync_with_arc(modeladmin, request, queryset):
    for instance in queryset:
        instance.update_arc_profile(commit=False)
        instance.load_first_login(commit=False)
        instance.save()


sync_with_arc.short_description = "Sincronizar con ARC"


def load_data_from_arc(modeladmin, request, queryset):
    for instance in queryset:
        instance.display_name = instance.profile["displayName"]
        instance.save()


load_data_from_arc.short_description = "Sincronizar con Middleware [Solo DisplayName]"


class EmptyDateRegisterFilter(admin.SimpleListFilter):
    title = "Fecha de registro en profile"
    parameter_name = "empty_date_register"

    def lookups(self, request, model_admin):
        return (("1", "Sin fecha de registro"),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(
                Q(profile="")
                | Q(profile=None)
                | Q(profile="null")
                | Q(profile__isnull=True)
                | Q(profile__createdOn="")
                | Q(profile__createdOn=None)
                | Q(profile__createdOn="null")
                | Q(profile__createdOn__isnull=True)
            )
        else:
            return queryset


class EmptyDateRegisterCreatedOnFilter(admin.SimpleListFilter):
    title = "Fecha de registro CreatedOn"
    parameter_name = "empty_date_register_created_on"

    def lookups(self, request, model_admin):
        return (("1", "Sin fecha de registro"),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(Q(created_on=None) | Q(created_on__isnull=True))
        else:
            return queryset


class MailTestFilter(admin.SimpleListFilter):
    title = "Emails de prueba"
    parameter_name = "test_email"

    def lookups(self, request, model_admin):
        return (("1", "Mailinator Email "),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(email__contains="mailinator.com")
        else:
            return queryset


class DataTreatmentFilter(admin.SimpleListFilter):
    title = "Tratamiento de datos"
    parameter_name = "data_treatment"

    def lookups(self, request, model_admin):
        return (("1", "Sin tratamiento de datos"),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.exclude(profile__contains=[{"name": "dataTreatment"}])
        else:
            return queryset


class EmailEmptyFilter(admin.SimpleListFilter):
    title = "Email vacio"
    parameter_name = "empty_email"

    def lookups(self, request, model_admin):
        return (
            ("1", "Email vacio sin reemplazar id facebook"),
            ("2", "Email vacio"),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(
                Q(profile__email="") | Q(
                    profile__email="null") | Q(profile__email=None)
            )
        elif self.value() == "2":
            list_users = []
            users = queryset.filter(
                Q(profile__email="") | Q(
                    profile__email="null") | Q(profile__email=None)
            )
            for user in users:
                identities = user.identities or user.first_login_identities
                for identity in identities:
                    if identity["type"] == "Facebook" and not identity["userName"]:
                        list_users.append(identity.uuid)
            if list_users:
                return queryset.filter(uuid__in=list_users)
            else:
                return queryset.none()
        else:
            return queryset


class EmailFacebookFilter(admin.SimpleListFilter):
    title = "Facebook Email"
    parameter_name = "facebook_email"

    def lookups(self, request, model_admin):
        return (
            ("1", "[Middleware] Facebook Email"),
            ("2", "[Middleware] Sin Facebook Email"),
            ("3", "[Arc] Facebook asociado"),
            ("4", "[Arc] Sin Facebook asociado"),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(
                Q(email__contains="facebook.com")
                | Q(profile__displayName__contains="facebook.com")
            )
        elif self.value() == "2":
            return queryset.exclude(
                Q(email__contains="facebook.com")
                | Q(profile__displayName__contains="facebook.com")
            )
        elif self.value() == "3":
            return queryset.filter(Q(first_login_method__contains="Facebook"))
        elif self.value() == "4":
            return queryset.exclude(Q(first_login_method__contains="Facebook"))
        else:
            return queryset


class IdentitiesFilter(admin.SimpleListFilter):
    title = "Vinculaciones del usuario"
    parameter_name = "identities_user"

    def lookups(self, request, model_admin):
        return (
            ("1", "Formulario"),
            ("2", "Facebook"),
            ("3", "Google"),
            ("4", "Facebook y Google"),
            ("5", "Formulario y Google"),
            ("6", "Formulario, Google y Facebook"),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(identities__contains=[{"type": "Password"}])
        elif self.value() == "2":
            return queryset.filter(identities__contains=[{"type": "Facebook"}])
        elif self.value() == "3":
            return queryset.filter(identities__contains=[{"type": "Google"}])
        elif self.value() == "4":
            return queryset.filter(
                identities__contains=[{"type": "Google"}, {"type": "Facebook"}]
            ).exclude(identities__contains=[{"type": "Password"}])
        elif self.value() == "5":
            return queryset.filter(
                identities__contains=[{"type": "Google"}, {"type": "Password"}]
            ).exclude(identities__contains=[{"type": "Facebook"}])
        elif self.value() == "6":
            return queryset.filter(
                identities__contains=[
                    {"type": "Google"},
                    {"type": "Password"},
                    {"type": "Facebook"},
                ]
            )
        else:
            return queryset


@admin.register(Promotion)
class PromotionAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = ("name",)


@admin.register(TokenUser)
class TokenUserAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = ("token",)


@admin.register(PromotionUser)
class PromotionUserAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = (
        "get_email",
        "get_promotion",
        "profile",
        "get_state",
    )
    list_filter = ("promotion__name",)
    search_fields = ("profile__email",)

    def get_promotion(self, obj):
        try:
            return obj.promotion.name
        except Exception:
            return ""

    def get_state(self, obj):
        try:
            if obj.state == PromotionUser.NEW_USER:
                return "Nuevo Usuario"
            elif obj.state == PromotionUser.EXISTS:
                return "Usuario Existente"
            else:
                return ""
        except Exception:
            return ""

    def get_email(self, obj):
        try:
            return obj.arc_user.email
        except Exception:
            return ""

    get_state.short_description = "Tipoo"
    get_promotion.shot_description = "Promocion"
    get_email.shot_description = "Email"


def export_csv_users(modeladmin, request, queryset):

    from django.utils.encoding import smart_str

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=report_users.csv"
    writer = csv.writer(response, csv.excel)
    response.write(
        u"\ufeff".encode("utf8")
    )  # BOM (optional...Excel needs it to open UTF-8 file properly)

    writer.writerow(
        [
            smart_str(u"uuid"),
            smart_str(u"email"),
            smart_str(u"Primer Portal"),
            smart_str(u"referer"),
            smart_str(u"Fecha de registro"),
            smart_str(u"Fecha de activacion de cuenta"),
            smart_str(u"Terminos y condiciones"),
            smart_str(u"Migrado de MPP"),
            smart_str(u"Dispositivo de login"),
            smart_str(u"Método de login"),
            smart_str(u"Acción para login"),
            smart_str(u"Identities"),
            smart_str(u"Perfil"),
        ]
    )
    for obj in queryset:
        try:
            email = obj.email
        except Exception as e:
            email = ""

        try:
            first_site = obj.first_site
        except Exception as e:
            first_site = ""

        try:
            list_attributes = obj.profile.get("attributes", []) or []
            referer = ""

            for attrib in list_attributes:
                if attrib.get("name", "") == "originReferer":
                    referer = attrib.get("value", "")
                    if not referer:
                        referer = "None"
        except Exception as e:
            referer = "None"

        try:
            date_created = timestamp_to_datetime(obj.profile.get("createdOn"))
            register_date = formats.date_format(
                date_created, settings.DATETIME_FORMAT)
        except Exception as e:
            register_date = "None"

        if obj.term_cond_pol_priv:
            term_cond_pol_priv = "acepto"
        else:
            term_cond_pol_priv = ""

        if obj.from_mpp:
            from_mpp = "migrado de mpp"
        else:
            from_mpp = ""

        writer.writerow(
            [
                smart_str(obj.uuid),
                smart_str(email),
                smart_str(first_site),
                smart_str(referer),
                smart_str(register_date),
                smart_str(date_to_localtime(obj.date_verified)),
                smart_str(term_cond_pol_priv),
                smart_str(from_mpp),
                smart_str(obj.first_login_device or ""),
                smart_str(obj.first_login_method or ""),
                smart_str(obj.first_login_action or ""),
                smart_str(obj.identities or ""),
                smart_str(obj.profile or ""),
            ]
        )
    return response


def keyset_pagination_iterator(input_queryset, batch_size=500):
    """
    The keyset_pagination_iterator() helper function accepts any
    queryset, orders it by the primary key and then repeatedly
    fetches 500 items. It then modifies the queryset to add a
    WHERE id > $last_seen_id clause. This is a relatively
    inexpensive way to paginate, so having an endpoint perform
    hat query dozens or even hundreds of times should hopefully
    avoid adding too much load to the database.
    """
    all_queryset = input_queryset.order_by("pk")
    last_pk = None
    while True:
        queryset = all_queryset
        if last_pk is not None:
            queryset = all_queryset.filter(pk__gt=last_pk)
        queryset = queryset[:batch_size]
        for row in queryset:
            last_pk = row.pk
            yield row
        if not queryset:
            break


def export_csv_users_action_v2(modeladmin, request, queryset):
    """
    Django Admin action for exporting selected rows as CSV
    Documentation:
    https://til.simonwillison.net/django/export-csv-from-django-admin
    """

    def rows(queryset):

        csvfile = StringIO()
        csvwriter = csv.writer(csvfile)
        columns = [field.name for field in modeladmin.model._meta.fields]

        def read_and_flush():
            csvfile.seek(0)
            data = csvfile.read()
            csvfile.seek(0)
            csvfile.truncate()
            return data

        header = False

        if not header:
            header = True
            csvwriter.writerow(columns)
            yield read_and_flush()

        for row in keyset_pagination_iterator(queryset):
            csvwriter.writerow(getattr(row, column) for column in columns)
            yield read_and_flush()

    response = StreamingHttpResponse(rows(queryset), content_type="text/csv")
    response["Content-Disposition"] = (
        "attachment; filename=%s.csv" % modeladmin.model.__name__
    )

    return response


def export_csv_deleted_users(modeladmin, request, queryset):

    from django.utils.encoding import smart_str

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=report_deleted_users.csv"
    writer = csv.writer(response, csv.excel)
    response.write(
        u"\ufeff".encode("utf8")
    )  # BOM (optional...Excel needs it to open UTF-8 file properly)

    writer.writerow(
        [
            smart_str(u"uuid"),
        ]
    )
    for obj in queryset:
        writer.writerow([smart_str(obj.arc_user.uuid)])
    return response


def send_request_users(modeladmin, request, queryset):
    token = TokenUser.objects.first()
    if settings.ENVIRONMENT == "production":
        domain = "https://elcomercio.arcpublishing.com"
    else:
        domain = "https://sandbox.elcomercio.arcpublishing.com"

    path_url = domain + "/identity/private/v1/task"
    headers = {
        "accept": "application/json",
        "accept-language": "es-ES,es;q=0.9,en;q=0.8",
        "arc-site": "elcomercio",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }
    cookies = {"Arc-Token": token.token}

    for obj in queryset:
        query = RequestDeleteUser.objects.filter(id_response=obj.id).exclude(
            Q(status="aprobado")
            | Q(status="PendingApproval")
            | Q(status="error")
            | Q(status="Declined")
        )
        if not query.exists():
            body = {"data": obj.uuid, "taskId": 4}
            r = requests.post(path_url, json=body,
                              headers=headers, cookies=cookies)

            try:
                result = r.json()
                delete_user = RequestDeleteUser(
                    id_response=result.get("id", ""),
                    status=result.get("status", ""),
                    data=result.get("data", {}),
                    arc_user=obj,
                )
                delete_user.save()
            except Exception as e:
                delete_user = RequestDeleteUser(
                    arc_user=obj,
                    data={**body, **cookies},
                    status="error",
                    log=r.text + "--error--" + str(e),
                )
                delete_user.save()


def approve_request(modeladmin, request, queryset):
    token = TokenUser.objects.first()
    headers = {
        "accept": "application/json",
        "accept-language": "es-ES,es;q=0.9,en;q=0.8",
        "arc-site": "elcomercio",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }
    cookies = {"Arc-Token": token.token}
    query = queryset.exclude(
        Q(status="aprobado") | Q(status="error") | Q(status="Declined")
    )

    if settings.ENVIRONMENT == "production":
        domain = "https://elcomercio.arcpublishing.com"
    else:
        domain = "https://sandbox.elcomercio.arcpublishing.com"

    for obj in query:
        path_url = domain + "/identity/private/v1/task/approve/" + \
            str(obj.id_response)
        r = requests.put(path_url, json={}, headers=headers, cookies=cookies)
        try:
            result = r.json()
            if result.get("id", ""):
                status = result.get("status")
            else:
                status = "error"

            delete_user = DeletedUser(
                id_response=result.get("id"),
                status=status,
                data=result.get("data"),
                arc_user=obj.arc_user,
                log=r.text + "--url--" + str(path_url),
            )
            delete_user.save()
            obj.status = "aprobado"
            obj.save()
        except Exception as e:
            request_delete_user = RequestDeleteUser(
                arc_user=obj.arc_user,
                status="error",
                data={**body, **cookies},
                log=r.text + "--error-- " + str(e),
            )
            request_delete_user.save()


def cancel_request(modeladmin, request, queryset):
    token = TokenUser.objects.first()
    headers = {
        "accept": "application/json",
        "accept-language": "es-ES,es;q=0.9,en;q=0.8",
        "arc-site": "elcomercio",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }
    cookies = {"Arc-Token": token.token}

    if settings.ENVIRONMENT == "production":
        domain = "https://elcomercio.arcpublishing.com"
    else:
        domain = "https://sandbox.elcomercio.arcpublishing.com"

    query = queryset.exclude(Q(status="aprobado") | Q(status="Declined"))
    for obj in query:
        path_url = domain + "/identity/private/v1/task/decline/" + \
            str(obj.id_response)
        payload = {"reason": "MISTAKE", "notes": ""}
        r = requests.put(path_url, json=payload,
                         headers=headers, cookies=cookies)
        try:
            result = r.json()
            if result.get("id", ""):
                status = result.get("status")
            else:
                status = "error"

            obj.status = status
            obj.log = r.text + "--url--" + str(path_url)
            obj.save()
        except Exception as e:
            request_delete_user = RequestDeleteUser(
                arc_user=obj.arc_user,
                status="error",
                data={**body, **cookies},
                log=r.text + "--error-- " + str(e),
            )
            request_delete_user.save()


send_request_users.short_description = u"Solicitud de eliminacion"
approve_request.short_description = u"Aprobacion de eliminacion"
cancel_request.short_description = u"Cancelar eliminacion"
export_csv_users.short_description = u"Export CSV"
export_csv_users_action_v2.short_description = u"Export CSV v2"


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


class StateUserFilter(admin.SimpleListFilter):
    title = "Estado del usuario"
    parameter_name = "state_user"

    def lookups(self, request, model_admin):
        return (
            ("1", "DeletedUsers: Eliminado"),
            ("2", "ReqDeletedUsers: Pendiente de eliminacion"),
            ("3", "DeletedUsers: No eliminados"),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(deletedusers__status="Ready")
        elif self.value() == "2":
            return queryset.filter(requestdeletes__status="PendingApproval").exclude(
                deletedusers__status="Ready"
            )
        elif self.value() == "3":
            return queryset.filter().exclude(
                Q(deletedusers__status="Ready")
                | Q(requestdeletes__status="PendingApproval")
            )
        else:
            return queryset


class ProfileStatusUserFilter(admin.SimpleListFilter):
    title = "Profile.status de ARC del usuario"
    parameter_name = "profile_status_user"

    def lookups(self, request, model_admin):
        return (("1", "Solo Profile.status='Active'"),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(profile__status__contains="Active")
        else:
            return queryset


class DisplayNameWithoutEmailFilter(admin.SimpleListFilter):
    title = "Display Name"
    parameter_name = "display_name_without_email"

    def lookups(self, request, model_admin):
        return (
            ("1", "Vacío o 'None'"),
            ("2", "Sin '@'"),
            ("3", "Sin '@' ni 'None'"),
            ("4", "Repetidos"),
            ("5", "Repetidos sin '@' ni 'None'"),
        )

    def queryset(self, request, queryset):

        if self.value() == "1":
            return queryset.filter(Q(display_name="") | Q(display_name__isnull=True))
        elif self.value() == "2":
            return queryset.exclude(display_name__contains="@")
        elif self.value() == "3":
            return queryset.filter().exclude(
                Q(display_name__contains="@")
                | Q(display_name="")
                | Q(display_name__isnull=True)
            )
        elif self.value() == "4":
            duplicates = (
                ArcUser.objects.values("display_name")
                .annotate(Count("display_name"))
                .order_by()
                .filter(display_name__count__gt=1)
            )
            return queryset.filter(
                display_name__in=[item["display_name"] for item in duplicates]
            )
        elif self.value() == "5":
            list_arc_filtered = queryset.filter().exclude(
                Q(display_name__contains="@")
                | Q(display_name="")
                | Q(display_name__isnull=True)
            )
            duplicates = (
                list_arc_filtered.values("display_name")
                .annotate(Count("display_name"))
                .order_by()
                .filter(display_name__count__gt=1)
            )
            return queryset.filter(
                display_name__in=[item["display_name"] for item in duplicates]
            )

        else:
            return queryset


class duplicatedFilter(admin.SimpleListFilter):
    title = "Duplicados"
    parameter_name = "duplicated"

    def lookups(self, request, model_admin):
        return (("1", "Profile.Email"),
                ("2", "Profile.DisplayName"),
                ("3", "Email"),
                )

    def queryset(self, request, queryset):
        if self.value() == "1":

            duplicates = (
                queryset.values("profile__email")
                .annotate(Count("profile__email"))
                .filter(profile__email__count__gt=1)
                .order_by("profile__email")
            )
            return (
                queryset.filter(
                    profile__email__in=[item["profile__email"]
                                        for item in duplicates]
                ).order_by("profile__email")
            )
        elif self.value() == "2":

            duplicates = (
                queryset.values("profile__display_name")
                .annotate(Count("profile__display_name"))
                .filter(profile__display_name__count__gt=1)
                .order_by("profile__display_name")
            )
            return (
                queryset.filter(
                    profile__display_name__in=[item["profile__display_name"]
                                               for item in duplicates]
                ).order_by("profile__display_name")
            )

        elif self.value() == '3':

            duplicates = (
                queryset.values("email")
                .annotate(Count("email"))
                .filter(email__count__gt=1)
                .order_by("email")
            )
            return (
                queryset.filter(
                    email__in=[item["email"]
                               for item in duplicates]
                ).order_by("email")
            )
        else:
            return queryset


class emailDateVerifiedFilter(admin.SimpleListFilter):
    title = "Fecha de verificación de email"
    parameter_name = "date_verified_email"

    def lookups(self, request, model_admin):
        return (("1", "Sin Fecha de Verificación"),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(date_verified=None)
        else:
            return queryset


class emailVerifiedFilter(admin.SimpleListFilter):
    title = "Email Verificado"
    parameter_name = "verified_email"

    def lookups(self, request, model_admin):
        return (
            ("1", "Verificado"),
            ("2", "No verificado"),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(email_verified=True)
        elif self.value() == "2":
            return queryset.exclude(email_verified=True)
        else:
            return queryset


class errorDisplayNameFilter(admin.SimpleListFilter):
    title = "Usuarios con error de DisplayName"
    parameter_name = "error_displayname"

    def lookups(self, request, model_admin):
        return (
            ("1", "Usuarios con error ahora mismo"),
            ("2", "Usuarios con error potencial pero sin estar afectado ahora"),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":

            list_arc_filtered = (
                queryset.filter(Q(profile__status__contains="Active"))
                .exclude(
                    Q(display_name__contains="@")
                    | Q(display_name="")
                    | Q(display_name__isnull=True)
                    | Q(first_login_method__contains="Facebook")
                    | Q(deletedusers__status="Ready")
                    | Q(requestdeletes__status="PendingApproval")
                )
                .order_by("display_name")
            )

            duplicates = (
                list_arc_filtered.values("display_name")
                .annotate(Count("display_name"))
                .filter(display_name__count__gt=1)
                .order_by("display_name")
            )
            return (
                queryset.filter(
                    display_name__in=[item["display_name"]
                                      for item in duplicates]
                )
                .exclude(
                    Q(display_name__contains="@")
                    | Q(display_name="")
                    | Q(display_name__isnull=True)
                    | Q(first_login_method__contains="Facebook")
                    | Q(deletedusers__status="Ready")
                    | Q(requestdeletes__status="PendingApproval")
                )
                .order_by("display_name")
            )

        elif self.value() == "2":

            return (
                queryset.filter(Q(profile__status__contains="Active"))
                .exclude(
                    Q(display_name__contains="@")
                    | Q(display_name="")
                    | Q(display_name__isnull=True)
                    | Q(first_login_method__contains="Facebook")
                    | Q(deletedusers__status="Ready")
                    | Q(requestdeletes__status="PendingApproval")
                )
                .order_by("display_name")
            )

        else:
            return queryset


@admin.register(ArcUser)
class ArcUserAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = (
        "get_display_name",
        "get_important_dates",
        "get_data",
        "get_origin_data",
        "get_date_reception",
    )
    list_filter = (
        ("created_on", DateTimeRangeFilter),
        ("date_verified", DateTimeRangeFilter),
        "first_site",
        DataTreatmentFilter,
        emailVerifiedFilter,
        emailDateVerifiedFilter,
        DisplayNameWithoutEmailFilter,
        "with_activity",
        MailTestFilter,
        StateUserFilter,
        ProfileStatusUserFilter,
        IdentitiesFilter,
        EmailFacebookFilter,
        "created_on",
        "first_login_device",
        "first_login_action",
        EmailEmptyFilter,
        EmptyDateRegisterFilter,
        EmptyDateRegisterCreatedOnFilter,
        "first_login_method",
        "with_subscription",
        errorDisplayNameFilter,
        duplicatedFilter,
    )
    search_fields = (
        "uuid",
        "email",
        "domain",
        "display_name",
    )
    actions = [
        sync_with_arc,
        load_data_from_arc,
        export_csv_users,
        export_csv_users_action_v2,
        send_request_users,
    ]

    formfield_overrides = {
        fields.JSONField: {"widget": JSONEditorWidget},
    }
    change_list_template = "admin/user_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("import-csv/", self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            reader = csv.reader(csv_file)

            # Create Hero objects from passed in data
            # ...
            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_form.html", payload)

    def changelist_view(self, request, extra_context=None):
        try:
            cl = self.get_changelist_instance(request)

        except Exception:
            pass

        else:
            if (
                "created_on__range__gte_0" not in request.GET
                or "created_on__range__lte_0" not in request.GET
            ):
                limit = timezone.now().date() - timedelta(days=45)
                queryset = cl.get_queryset(
                    request).filter(created_on__gte=limit)

            else:
                queryset = cl.get_queryset(request)

            # Aggregate new subscribers per day
            chart_data = (
                queryset.annotate(date=TruncDay("created_on"))
                .values("date")
                .annotate(y=Count("id"))
                .order_by("-date")
            )

            # Serialize and attach the chart data to the template context
            as_json = json.dumps(list(chart_data), cls=DjangoJSONEncoder)
            extra_context = extra_context or {"chart_data": as_json}

        # Call the superclass changelist_view to render the page
        return super().changelist_view(request, extra_context=extra_context)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_display_name(self, obj):
        if obj.email_verified:
            symbol = "check"
            email_verified = "Verificado"
        else:
            symbol = "times"
            email_verified = "No verificado"

        try:
            display_name = obj.display_name
        except Exception as e:
            display_name = ""

        return format_html(
            "{full_name}</br>"
            "DisplayName:{display_name}</br>"
            '<i class="fas fa-fingerprint"></i> {uuid}</br>'
            '<i class="fas fa-at"></i> {email}</br>'
            '<i class="fas fa-newspaper"></i> {site}</br>'
            '<i class="fas fa-user-{symbol}"></i> {email_verified}',
            full_name=self.get_fullname(obj),
            uuid=obj.uuid,
            email=self.get_email(obj),
            site=obj.first_site or "--",
            email_verified=email_verified,
            symbol=symbol,
            display_name=display_name,
        )

    def get_date_reception(self, obj):
        return format_html(
            "Fecha de recepción: {created}</br>"
            "Fecha de actualizacion: {last_updated}",
            created=obj.created,
            last_updated=obj.last_updated,
        )

    def get_username(self, obj):
        if obj.identities:
            username = []
            for identity in obj.identities:
                username.append(identity.get("username", ""))
            return username

    def get_email(self, obj):
        if obj.profile:
            if obj.profile.get("email") and obj.profile.get("email") != "null":
                return obj.profile.get("email")
            else:
                identities = obj.identities or obj.first_login_identities
                for identity in identities:
                    if identity["type"] == "Facebook":
                        email = "{}@facebook.com".format(identity["userName"])
                        return email
                else:
                    return ""

    def get_fullname(self, obj):
        if obj.profile:
            first_name = obj.profile.get("firstName") or ""
            last_name = obj.profile.get("lastName") or ""
            second_last_name = obj.profile.get("secondLastName") or ""
            if first_name or last_name or second_last_name:
                full_name = "{} {} {}".format(
                    first_name, last_name, second_last_name)
            else:
                full_name = ""
            return Truncator(full_name).chars(50)

    def get_important_dates(self, obj):
        date_created = obj.profile.get("createdOn")
        date_created = timestamp_to_datetime(date_created)

        modified_on = obj.profile.get("modifiedOn")
        modified_on = timestamp_to_datetime(modified_on)

        date_verified = (
            obj.date_verified.astimezone(timezone.get_current_timezone())
            if obj.date_verified
            else None
        )

        tz_first_login = (
            obj.first_login.astimezone(timezone.get_current_timezone())
            if obj.first_login
            else None
        )

        tz_last_login = self.get_last_login(obj)

        return format_html(
            "<b>Registro:</b> {}</br>"
            "<b>Fecha de verificación:</b> {}</br>"
            "<b>Actualización:</b> {}</br>"
            "<b>Primer login:</b> {}</br>"
            "<b>Último login:</b> {}</br>",
            formats.date_format(date_created, settings.DATETIME_FORMAT)
            if date_created
            else "--",
            formats.date_format(date_verified, settings.DATETIME_FORMAT)
            if date_verified
            else "--",
            formats.date_format(modified_on, settings.DATETIME_FORMAT)
            if modified_on
            else "--",
            formats.date_format(tz_first_login, settings.DATETIME_FORMAT)
            if tz_first_login
            else "--",
            formats.date_format(tz_last_login, settings.DATETIME_FORMAT)
            if tz_last_login
            else "--",
        )

    def get_last_login(self, obj):
        last_login = 0
        if obj.identities:
            for identity in obj.identities:
                if (
                    identity.get("lastLoginDate")
                    and identity.get("lastLoginDate") > last_login
                ):
                    last_login = identity.get("lastLoginDate")
            if last_login:
                return datetime.fromtimestamp(last_login / 1000)

    def get_data(self, obj):
        list_identity = ""
        start_itentity = 1
        if obj.identities:
            for identity in obj.identities:
                if start_itentity:
                    start_itentity = 0
                    list_identity = identity.get("type")
                else:
                    list_identity = list_identity + ", " + identity.get("type")

        return format_html(
            "Vinculos: <strong>{list_identity}</strong></br>"
            "Método: <strong>{first_login_method}</strong></br>"
            "Dispositivo: <strong>{first_login_device}</strong></br>"
            "Acción: <strong>{first_login_action}</strong></br>",
            first_login_method=obj.first_login_method or "--",
            first_login_device=obj.first_login_device or "--",
            first_login_action=obj.first_login_action or "--",
            list_identity=list_identity,
        )

    def get_origin_data(self, obj):
        list_attributes = obj.profile.get("attributes", []) or []
        referer = ""
        origin_action = ""
        from_mpp = ""
        statusarc = obj.profile.get("status", "") or ""
        for attrib in list_attributes:
            if attrib.get("name", "") == "originReferer":
                referer = attrib.get("value", "")

            if attrib.get("name", "") == "originAction":
                origin_action = attrib.get("value", "")

            if attrib.get("name", "") == "fromMPP":
                from_mpp = attrib.get("value", "")

        if DeletedUser.objects.filter(arc_user=obj, status="Ready").exists():
            state = "Eliminado"
        elif RequestDeleteUser.objects.filter(
            arc_user=obj, status="PendingApproval"
        ).exists():
            state = "Pendiente de Eliminacion"
        else:
            state = "Activo"

        return format_html(
            "<b>Dominio:</b> {domain}</br>"
            "<b>originAction:</b> {origin_action}</br>"
            "<b>originReferer:</b> {referer}</br>"
            "<b>Origen:</b> {origin}</br>"
            "<b>Condiciones:</b> {terms}</br>"
            "<b>Estado:</b> {state}</br>"
            "<b>Profile.status:</b> {statusarc}</br>"
            "<b>fromMPP:</b> {from_mpp}</br>",
            domain=obj.domain or "--",
            origin_action=origin_action,
            origin=self.get_origin_sso(obj) or "--",
            terms=obj.term_cond_pol_priv or "--",
            referer=referer,
            state=state,
            statusarc=statusarc,
            from_mpp=from_mpp,
        )

    def get_origin_sso(self, obj):
        if obj.from_mpp is True:
            return "MPP"
        elif obj.from_mpp is False:
            return "ARC"
        else:
            return "--"

    get_display_name.short_description = "Usuario"
    get_important_dates.short_description = "Fechas importantes"
    get_data.short_description = "Fuente"
    get_origin_data.short_description = "Datos"
    get_date_reception.short_description = "Fechas recepcion"


"""
@admin.register(ArcUserDeletedProxyModel)
class ArcUserDeletedProxyModelAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = (
        'uuid',
        'email',
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(domain='')
"""


@admin.register(DeletedUser)
class DeletedUserAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = ("get_display_name", "data", "id_response", "status", "log")

    list_filter = ("status",)
    search_fields = ("arc_user__uuid",)
    actions = [export_csv_deleted_users]

    def get_display_name(self, obj):
        return format_html(
            "{full_name}</br>"
            '<i class="fas fa-fingerprint"></i> {uuid}</br>'
            '<i class="fas fa-at"></i> {email}</br>'
            '<i class="fas fa-newspaper"></i> {site}</br>',
            full_name=self.get_fullname(obj.arc_user),
            uuid=obj.arc_user.uuid,
            email=obj.arc_user.email,
            site=obj.arc_user.first_site or "--",
        )

    def get_fullname(self, obj):
        if obj.profile:
            first_name = obj.profile.get("firstName") or ""
            last_name = obj.profile.get("lastName") or ""
            second_last_name = obj.profile.get("secondLastName") or ""
            if first_name or last_name or second_last_name:
                full_name = "{} {} {}".format(
                    first_name, last_name, second_last_name)
            else:
                full_name = ""
            return Truncator(full_name).chars(50)


@admin.register(RequestDeleteUser)
class RequestDeleteUserAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = ("get_display_name", "data", "id_response", "status", "log")
    actions = [approve_request, cancel_request]
    readonly_fields = ("arc_user",)
    list_filter = ("status",)
    search_fields = ("arc_user__uuid",)

    def get_display_name(self, obj):
        return format_html(
            "{full_name}</br>"
            '<i class="fas fa-fingerprint"></i> {uuid}</br>'
            '<i class="fas fa-at"></i> {email}</br>'
            '<i class="fas fa-newspaper"></i> {site}</br>',
            full_name=self.get_fullname(obj.arc_user),
            uuid=obj.arc_user.uuid,
            email=obj.arc_user.email,
            site=obj.arc_user.first_site or "--",
        )

    def get_fullname(self, obj):
        if obj.profile:
            first_name = obj.profile.get("firstName") or ""
            last_name = obj.profile.get("lastName") or ""
            second_last_name = obj.profile.get("secondLastName") or ""
            if first_name or last_name or second_last_name:
                full_name = "{} {} {}".format(
                    first_name, last_name, second_last_name)
            else:
                full_name = ""
            return Truncator(full_name).chars(50)


@admin.register(LogArcUserReport)
class LogArcUserReportAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = (
        "get_start_date",
        "get_end_date",
        "get_job_id",
        "get_status",
        "download_total",
        "site",
    )
    list_filter = ("site",)

    def get_start_date(self, obj):
        try:
            return obj.schedule_request.get("startDate", "")
        except Exception:
            return ""

    def get_end_date(self, obj):
        try:
            return obj.schedule_request.get("endDate", "")
        except Exception:
            return ""

    def get_job_id(self, obj):
        try:
            return obj.schedule_response.get("jobID", "")
        except Exception:
            return ""

    def get_status(self, obj):
        try:
            return obj.schedule_response.get("status", "")
        except Exception:
            return ""

    get_start_date.short_description = "Fecha de inicio"
    get_end_date.short_description = "Fecha de Fin"
    get_job_id.short_description = "Job Id"
    get_status.short_description = "Estado"


class UserEmptyFilter(admin.SimpleListFilter):
    title = "User vacio"
    parameter_name = "empty_user"

    def lookups(self, request, model_admin):
        return (("1", "User no cargado"),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(user=None)
        else:
            return queryset


@admin.register(ArcUserReport)
class ArcUserReportAdmin(_AuditedModelMixin, admin.ModelAdmin):
    list_display = (
        "uuid",
        "last_modified_date",
        "last_login_date",
        "created_on",
        "site",
        "user",
    )
    list_filter = (
        ("created_on", DateTimeRangeFilter),
        "site",
        UserEmptyFilter,
    )
    search_fields = ("uuid",)
