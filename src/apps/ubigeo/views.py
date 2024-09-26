# -*- coding: utf-8 -*-

import sys
import json

from django.conf import settings
from django.views.generic import TemplateView, FormView, ListView
#from apps.checkout.forms.pasarela import *
from mixins.json_response_mixin import JSONResponseMixin
from apps.ubigeo.models import Ubigeo


class AddressGetDistrictsView(JSONResponseMixin, TemplateView):
    def render_to_response(self, context, **response_kwargs):
        code = self.kwargs.get('code', None)
        codes = code.split('-')
        department_code = codes[0]
        province_code = codes[1]
        districts = Ubigeo.objects.filter(estado=1, ubigeo_provc=province_code, ubigeo_depc=department_code). \
            exclude(ubigeo_disc='00').values('id', 'ubigeo_disn')
        response_data = dict()
        response_data['districts'] = list(districts)
        return self.render_to_json_response(response_data, **response_kwargs)