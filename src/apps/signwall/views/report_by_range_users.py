import csv
from datetime import datetime, timedelta

# from functools import reduce
# from operator import and_
from django.db.models import Q, Count
from django.http import HttpResponse
from django.template import loader
from django.views import View
from django.contrib.postgres.aggregates.general import StringAgg

import pytz

from apps.arcsubs.models import ArcUser
from apps.signwall.forms import RangeDateForm


TIMEZONE = pytz.timezone('America/Lima')


class UserByRangeReport(View):
    """
        Debe registrar el contenido de las notificaciones que posteriormente se debe procesar.
    """

    def get(self, request, *args, **kwargs):
        template = loader.get_template('admin/report/users_total.html')
        sites = {1: 1}
        context = {
            'form': RangeDateForm,
            'sites': sites
        }
        return HttpResponse(template.render(context, request))

    def post(self, request, *args, **kwargs):
        year_begin = 2019
        year_end = 2020
        month_begin = 2
        month_end = 4
        site = 1
        # 'https://stackoverflow.com/questions/14077799/django-filter-by-specified-month-and-year-in-date-range'
        arc_user_row = ArcUser.objects.filter(
            created_on__year__gte=year_begin, created_on__year__lte=year_end,
            created_on__month__gte=month_begin, created_on__month__lte=month_end,
            site=site
        )
