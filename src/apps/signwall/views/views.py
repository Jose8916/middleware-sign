import csv
from datetime import datetime, timedelta

# from functools import reduce
# from operator import and_
from django.db.models import Q, Count
from django.http import HttpResponse
from django.template import loader
from django.views import View
from django.contrib.postgres.aggregates.general import StringAgg, ArrayAgg

import pytz

from apps.arcsubs.models import ArcUser, DeletedUser
from apps.signwall.forms import RangeDateForm


TIMEZONE = pytz.timezone('America/Lima')


class UserByDateReport(View):
    """
        Debe registrar el contenido de las notificaciones que posteriormente se debe procesar.
    """

    def get(self, request, *args, **kwargs):
        template = loader.get_template('admin/report/user_by_date.html')
        sites = {1: 1}
        context = {
            'form': RangeDateForm,
            'sites': sites
        }
        return HttpResponse(template.render(context, request))

    def get_day(self, date_format):
        list_date_start = str(date_format).split('-')
        list_day = (list_date_start[2]).split(' ')
        return list_day[0]

    def day_start(self, date_format):
        list_date_start = str(date_format).split('-')
        list_day = (list_date_start[2]).split(' ')
        date_start = list_date_start[0] + '-' + list_date_start[1] + '-' + list_day[0]
        return int(datetime.datetime.strptime(date_start + " 00:01", "%Y-%m-%d %H:%M").strftime("%s")) * 1000

    def day_end(self, date_format):
        list_date_end = str(date_format).split('-')
        list_day = (list_date_end[2]).split(' ')
        date_end = list_date_end[0] + '-' + list_date_end[1] + '-' + list_day[0]
        return int(datetime.datetime.strptime(date_end + " 23:59", "%Y-%m-%d %H:%M").strftime("%s")) * 1000

    def date_start_timestamp(self, date_start):
        list_date_start = str(date_start).split('/')
        date_start = list_date_start[2] + '-' + list_date_start[1] + '-' + list_date_start[0]
        print(date_start)
        start = datetime.combine(
            datetime.strptime(date_start, "%Y-%m-%d"),
            datetime.min.time()
        )
        return TIMEZONE.localize(start)

    def date_end_timestamp(self, date_end):
        list_date_end = str(date_end).split('/')
        date_end = list_date_end[2] + '-' + list_date_end[1] + '-' + list_date_end[0]
        end = datetime.combine(
            datetime.strptime(date_end, "%Y-%m-%d"),
            datetime.max.time()
        )
        return TIMEZONE.localize(end)

    def generate_csv(self, date_start, date_end):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_report.csv"'

        writer = csv.writer(response)
        # users = ArcUser.objects.filter(profile__createdOn__range=(date_start_timestamp, date_end_timestamp))
        users = ArcUser.objects.filter(created_on__range=(self.date_start_timestamp(date_start), self.date_end_timestamp(date_end)))

        list_titles = ['Identificador de usuario UUID', 'Email', 'event_type', 'profile', 'Identities',
                       'arc_state', 'Domain']

        names_attributes = {
            # ('name', 'elementos'),
            'mppId': '1',
            'mppStatus': '1',
            'mppCreated': '1',
            'mppClientUserId': '1',
            'mppLastUpdated': '1',
            'academicLevel': '1',
            'originMethod': '1',
            'ageRange': '1',
            'civilStatus': {'SO': 'Soltero', 'CA': 'Casado', 'DI': 'Divorciado (a)', 'VI': 'Viudo (a)'},
            'originDevice': '1',
            'oldEmailHash': '1',
            'emailHash': '1',
            'documentNumber': '1',
            'originDomain': '1',
            'fromEcoid': '1',
            'work': '1',
            'originReferer': '1',
            'mppSocialId': '1',
            'documentType': '1',
            'originAction': '1',
            'originUserAgent': '1',
            'userStatus': '1',
            'workArea': '1',
            'workStation': '1',
            'mobilePhone': '1',
            'phone': '1',
            'district': '1',
            'province': '1',
            'country': '1',
            'fromMPP': '1',
            'mppVerified': '1',
            'department': '1',
            'birthdate': '1'
        }
        names_attributes_keys = list(names_attributes.keys())
        writer.writerow(list_titles + names_attributes_keys + ['Fecha de Registro', 'modifiedOn', 'new_fromMPP'])

        list_row = []
        list_attributes = []
        valor = ''
        register_date = ''
        modified_date = ''

        for user in users:
            if user.profile:
                if user.profile.get('attributes', ''):
                    list_attributes = []
                    for key in names_attributes_keys:
                        for attrib in user.profile.get('attributes', ''):
                            if key == attrib.get('name'):
                                valor = attrib.get('value', '')

                        list_attributes.append(valor)
                        valor = ''
            lista_last_login = []
            if user.identities:
                if len(user.identities):
                    for identity in user.identities:
                        if identity.get('lastLoginDate', ''):
                            lista_last_login.append(int(identity.get('lastLoginDate', '')))

                    # if lista_last_login and lista_last_login != [None]:
                    #     last_login_uTimestamp = max(lista_last_login)
                    #     last_login_format = datetime.fromtimestamp(last_login_uTimestamp / 1000.0)
                    # else:
                    #     last_login_format = ''

            if user.profile.get('createdOn', ''):
                register_date = datetime.fromtimestamp(user.profile.get('createdOn', '') / 1000.0)

            if user.profile.get('modifiedOn', ''):
                modified_date = datetime.fromtimestamp(user.profile.get('modifiedOn', '') / 1000.0)

            list_row = [user.uuid, user.email, user.event_type, user.profile, user.identities,
                        user.arc_state, user.domain]

            writer.writerow(list_row + list_attributes + [user.created_on, modified_date, user.from_mpp])
        return response

    def range_to_timestamp(self, start_date, end_date):
        starts = datetime.combine(
            start_date,
            datetime.min.time()
        )
        ends = datetime.combine(
            end_date,
            datetime.max.time()
        )
        return (
            TIMEZONE.localize(starts),
            TIMEZONE.localize(ends)
        )

    def get_queryset_base(self, start_date, end_date, form):
        domain = form.cleaned_data.get('domain')
        device = form.cleaned_data.get('device')
        action = form.cleaned_data.get('origin_action')

        queryset = ArcUser.objects.filter(
            created_on__range=self.range_to_timestamp(start_date, end_date)
        )

        if domain:
            if domain == 'unknown':
                queryset = queryset.filter(Q(domain='') | Q(domain='undefined') | Q(domain=None))
            else:
                queryset = queryset.filter(domain=domain)

        if device:
            if device == 'unknown':
                queryset = queryset.filter(Q(first_login_device='') | Q(first_login_device=None))
            else:
                queryset = queryset.filter(first_login_device=device)

        if action:
            if device == 'unknown':
                queryset = queryset.filter(Q(first_login_action='') | Q(first_login_action=None))
            else:
                queryset = queryset.filter(first_login_action=action)

        return queryset
        # concatenar = []
        # if site:
        #     concatenar.append(Q(domain=settings.DOMAIN_DIC.get(site)))

        # if type_register:
        #     concatenar.append(Q(profile__attributes__contains=[{'name': 'originMethod', 'value': type_register}]))

        # if origin_device:
        #     concatenar.append(Q(profile__attributes__contains=[{'name': 'originDevice', 'value': origin_device}]))

        # if method_register:
        #     concatenar.append(Q(profile__attributes__contains=[{'name': 'originAction', 'value': origin_device}]))

        # if concatenar:
        #     return ArcUser.objects.filter(Q(profile__createdOn__range=(date_start_timestamp, date_end_timestamp)) &
        #                                   reduce(and_, [c for c in concatenar])).count()
        # else:
        #     return ArcUser.objects.filter(profile__createdOn__range=(date_start_timestamp, date_end_timestamp)).count()

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'download_csv':
            date_start = request.POST.get('start_date', '')
            date_end = request.POST.get('end_date')

            # date_start_timestamp = int(
            #     datetime.strptime(date_start + " 00:00", "%d/%m/%Y %H:%M").strftime("%s")) * 1000
            # date_end_timestamp = int(
            #     datetime.strptime(date_end + " 23:59", "%d/%m/%Y %H:%M").strftime("%s")) * 1000

            return self.generate_csv(date_start, date_end)

        else:
            form = RangeDateForm(request.POST or None)

            table_data = []
            table_headers = (
                'Día',
                'MPP (Antiguos)',
                'MPP > Facebook',
                'MPP > Password',
                # 'MPP > Otro login',
                'MPP > Sin login',
                'ARC (Nuevos)',
                'ARC > Facebook',
                'ARC > Password',
                # 'ARC > Otro login',
                'ARC > Sin login',
                'Total creados',
            )
            table_foot = []
            if form.is_valid():
                start_date = form.cleaned_data.get('start_date')
                end_date = form.cleaned_data.get('end_date')

                delta = end_date - start_date
                for count in range(delta.days + 1):
                    day = start_date + timedelta(days=count)
                    queryset_base = self.get_queryset_base(day, day, form)

                    queries = self.get_row_data(queryset_base)
                    row = {'Día': day}
                    for header in table_headers:
                        if header in queries:
                            row[header] = queries[header]

                    table_data.append(row)

                queryset_base = self.get_queryset_base(start_date, end_date, form)
                queries = self.get_row_data(queryset_base)
                table_foot = ['', ]
                for header in table_headers:
                    if header in queries:
                        value = queries[header]
                        table_foot.append('%s</br>%s' % (header, value))
            else:
                print(form.errors)

            context = {
                'form': form,
                'table_headers': table_headers,
                'table_data': table_data,
                'table_foot': table_foot,
            }
            template = loader.get_template('admin/report/user_by_date.html')
            return HttpResponse(template.render(context, request))

    def get_row_data(self, query):
        from_mpp = query.filter(from_mpp=True)
        mpp_facebook = from_mpp.filter(first_login_method='Facebook')
        mpp_password = from_mpp.filter(first_login_method='Password')
        mpp_none = from_mpp.exclude(first_login=None).exclude(
            Q(first_login_method='Facebook') | Q(first_login_method='Password')
        )
        mpp_pending = from_mpp.filter(first_login=None)

        from_arc = query.exclude(from_mpp=True)
        arc_facebook = from_arc.filter(first_login_method='Facebook')
        arc_password = from_arc.filter(first_login_method='Password')
        arc_none = from_arc.exclude(first_login=None).exclude(
            Q(first_login_method='Facebook') | Q(first_login_method='Password')
        )
        arc_pending = from_arc.filter(first_login=None)

        row = {
            'Total creados': query.count(),
            'MPP (Antiguos)': from_mpp.count(),
            'ARC (Nuevos)': from_arc.count(),
            'MPP > Facebook': mpp_facebook.count(),
            'MPP > Password': mpp_password.count(),
            'MPP > Otro login': mpp_none.count(),
            'MPP > Sin login': mpp_pending.count(),
            'ARC > Facebook': arc_facebook.count(),
            'ARC > Password': arc_password.count(),
            'ARC > Otro login': arc_none.count(),
            'ARC > Sin login': arc_pending.count(),
        }
        return row


class UsersRepeatedReport(View):
    """
        Cantidad de usuarios repetidos
    """

    def get(self, request, *args, **kwargs):
        template = loader.get_template('admin/report/users_repeated.html')
        query_string = 'SELECT  1 as id , email, string_agg( to_char("created_on", \'DD/MM/YYYY HH12:MIPM\') || \' - \' || domain, \', \') as fecha_creacion, COUNT(email) as dcount FROM arcsubs_arcuser GROUP BY (email) HAVING (COUNT(email))>1'
        #users = ArcUser.objects.values('email').annotate(
        #    dcount=Count('email'), fecha_creacion=StringAgg('domain || \' \' || domain', delimiter=','))\
        #    .filter(dcount__gt=1)
        users = ArcUser.objects.raw(query_string)

        context = {
            'users': users
        }
        return HttpResponse(template.render(context, request))


class DisplayNameRepeatedReport(View):
    """
        Cantidad de usuarios repetidos
    """

    def get(self, request, *args, **kwargs):
        template = loader.get_template('admin/report/display_name_users_repeated.html')

        query_string = 'SELECT  1 as id , display_name, string_agg( to_char("created_on", \'DD/MM/YYYY HH12:MIPM\') || \' * \' || domain || \' * \' || email || \' * \' || uuid, \', \') as fecha_creacion, COUNT(display_name) as dcount FROM arcsubs_arcuser GROUP BY (display_name) HAVING (COUNT(display_name))>1'
        users = ArcUser.objects.raw(query_string)

        list_user = []
        for user in users:
            dict_user = {}
            tosplit = user.fecha_creacion
            if tosplit:
                data_user = tosplit.split(',')
            else:
                data_user = ''

            dict_user['display_name'] = user.display_name
            dict_user['dcount'] = user.dcount
            dict_user['data'] = data_user
            list_user.append(dict_user)

        context = {
            'users': list_user
        }
        return HttpResponse(template.render(context, request))
