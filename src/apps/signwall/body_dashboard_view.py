import csv
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from django.views import View


import pytz

from apps.arcsubs.models import ArcUser, ArcUserReport
from apps.signwall.forms import RangeDateForm
from apps.signwall.utils import list_last_month

TIMEZONE = pytz.timezone('America/Lima')


class BodyDashboard(View):
    """

    """

    def get(self, request, *args, **kwargs):
        template = loader.get_template('admin/report/body_dashboard.html')
        total_users = ArcUser.objects.count()
        total_users_arc = ArcUserReport.objects.count()
        vinculo_users_facebook = ArcUser.objects.filter(identities__contains=[{'type': 'Facebook'}]).count()
        vinculo_users_google = ArcUser.objects.filter(identities__contains=[{'type': 'Google'}]).count()
        vinculo_users_formulario = ArcUser.objects.filter(identities__contains=[{'type': 'Password'}]).count()

        context = {
            'total_users': total_users,
            'total_users_arc': total_users_arc,
            'vinculo_users_facebook': vinculo_users_facebook,
            'vinculo_users_google': vinculo_users_google,
            'vinculo_users_formulario': vinculo_users_formulario,
            'list_last_month': list_last_month(6)
        }
        
        return HttpResponse(template.render(context, request))
