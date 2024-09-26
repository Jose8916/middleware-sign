# coding=utf-8

from datetime import datetime

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ....arcsubs.models import SendMail

class ApiEventsRegisterMailingView(APIView):

    def post(self, request):
        data = request.data
        date_now = datetime.now()
        if data['is_send']:
            SendMail.objects.create(
                state=True,
                email=data['email'],
                data=data['params'],
                html=data['html'],
                event_type=data['type'],
                send=date_now,
                response=data['response']
            )
        else:
            SendMail.objects.create(
                email=data['email'],
                data=data['params'],
                html=data['html'],
                event_type=data['type'],
            )
        return Response({'register': True}, status=status.HTTP_200_OK)

