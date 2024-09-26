from datetime import datetime, timedelta
from django.shortcuts import render
from django.db.models import Q, Count, DateTimeField
from django.http import HttpResponse
from django.template import loader
from django.views import View
from apps.arcsubs.utils import start_today_date
from django.utils.timezone import get_default_timezone
from apps.arcsubs.models import ArcUser
from django.db.models.functions import TruncDay, Trunc
from django.utils import timezone
import json
import pytz

TIMEZONE = pytz.timezone('America/Lima')


class VerifiedUsers(View):
    """

    """
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
            starts.astimezone(TIMEZONE),
            ends.astimezone(TIMEZONE)
        )

    def min_date(self, date_input):
        min_date = datetime.combine(
            date_input,
            datetime.min.time()
        )
        return min_date.astimezone(TIMEZONE),

    def get(self, request, *args, **kwargs):
        template = loader.get_template('admin/report/verified_users.html')
        list_color = [
            'rgb(0, 0, 255)',  # BLUE  # 0000FF
            'rgb(192, 192, 192)',  # silver
            'rgb(0, 0, 0)',  # BLACK  # 000000
            'rgb(255, 0, 0)'  # RED  # FF0000
        ]
        start_date = datetime.now(TIMEZONE) - timedelta(days=30)
        end_date = datetime.now(TIMEZONE)
        range_date_search = end_date - start_date

        list_days = []

        for count in range(range_date_search.days + 1):
            day = start_date + timedelta(days=count)

            users = ArcUser.objects.filter(
                date_verified__range=self.range_to_timestamp(day, day)
            ).exclude(date_verified__isnull=True)

            list_days.append({
                'name': day.strftime("%Y-%m-%d"),
                'count': users.count(),
                'cantidad_face': users.filter(first_login_method='Facebook').count(),
                'cantidad_google': users.filter(first_login_method='Google').count(),
                'cantidad_pass': users.filter(first_login_method='Password').count()
            })

        # armando grafico
        data_graph = {
            'labels': [sub['name'] for sub in list_days],
            'datasets': [{
                'label': 'Activaciones de cuenta',
                'backgroundColor': list_color[0],
                'borderColor': list_color[0],
                'data': [sub['count'] for sub in list_days]
            }]
        }

        context = {
            'data_graph': data_graph,
            'type_report': 'fallecidos',
            'start_date': start_date.strftime("%d-%m-%Y"),
            'end_date': end_date.strftime("%d-%m-%Y"),
            'reportes': list_days
        }
        return HttpResponse(template.render(context, request))

    def post(self, request, *args, **kwargs):
        template = loader.get_template('admin/report/verified_users.html')
        list_color = [
            'rgb(0, 0, 255)',  # BLUE  # 0000FF
            'rgb(192, 192, 192)',  # silver
            'rgb(0, 0, 0)',  # BLACK  # 000000
            'rgb(255, 0, 0)'  # RED  # FF0000
        ]
        type_login = request.POST.get('type_login', '')
        start_date = datetime.now(TIMEZONE) - timedelta(days=30)
        end_date = datetime.now(TIMEZONE)

        range_date_search = end_date - start_date

        list_days = []

        for count in range(range_date_search.days + 1):
            list_user = []
            print('---------------')
            print(start_date)
            day = start_date + timedelta(days=count)
            """
            users = ArcUser.objects.filter(
                date_verified__range=self.range_to_timestamp(day, day)
            )
            """
            users = ArcUser.objects.exclude(date_verified__isnull=True)\
                .annotate(
                    start_day=Trunc('date_verified', 'day', output_field=DateTimeField(), tzinfo=TIMEZONE)
                ).filter(
                    start_day__year=day.year,
                    start_day__month=day.month,
                    start_day__day=day.day
            )
            if type_login:
                users.filter(first_login_method=type_login)

            list_user.append(day)

            list_days.append({
                'name': day.strftime("%Y-%m-%d"),
                'count': users.count()
            })

        # armando grafico
        data_graph = {
            'labels': [sub['name'] for sub in list_days],
            'datasets': [{
                'label': 'Verificaciones de de cuenta',
                'backgroundColor': list_color[0],
                'borderColor': list_color[0],
                'data': [sub['count'] for sub in list_days]
            }]
        }

        context = {
            'data_graph': data_graph,
            'type_report': 'fallecidos',
            'start_date': start_date.strftime("%d-%m-%Y"),
            'end_date': end_date.strftime("%d-%m-%Y"),
            'users': list_days
        }
        return HttpResponse(template.render(context, request))
