from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone

from apps.signwall.models import UsersReport
from apps.arcsubs.models import ArcUser


class Command(BaseCommand):
    help = 'Update fields users'

    def format_date(self, createdOn):
        createdOn_format = datetime.strptime(createdOn, "%Y-%m-%d %H:%M:%S")
        return get_default_timezone().localize(createdOn_format)

    def add_arguments(self, parser):
        parser.add_argument('--startDate', nargs='?', type=str)
        parser.add_argument('--endDate', nargs='?', type=str)

    def handle(self, *args, **options):
        users = UsersReport.objects.all()
        for user in users:
            # print(user.user_profile.get('clientId', ''))
            ArcUser.objects.filter(
                uuid=user.user_profile.get('clientId', '')
            ).exclude(
                created_on__isnull=False
            ).update(
                created_on=self.format_date(user.user_profile.get('createdOn', ''))
            )
        print('actualizacion correcta')
