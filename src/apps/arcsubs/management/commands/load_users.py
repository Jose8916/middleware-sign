from django.core.management.base import BaseCommand

from ...models import ArcEvent, ArcUser
from ...arcclient import ArcClientAPI


class Command(BaseCommand):
    help = 'Ejecuta el comando'

    def handle(self, *args, **options):
        events = ArcEvent.objects.filter(
            processed=False,
            event_type__in=('SIGNUP_EDIT', 'PROFILE_EDIT', 'PASSWORD_RESET_REQUEST')
        )[:10]
        client = ArcClientAPI()

        for event in events:
            defaults = {}
            uuid = event.message.get('uuid')
            if event.message.get('email'):
                defaults['email'] = event.message.get('email')

            process = False
            if event.event_type == 'SIGNUP_EDIT' or event.event_type == 'PROFILE_EDIT':
                arc_user, created = ArcUser.objects.get_or_create(
                    uuid=uuid,
                    defaults=defaults
                )
                data = client.get_profile_by_uuid(uuid)

                arc_user.profile = data['profile']
                arc_user.email = data['profile']['email']
                arc_user.identity = data['identity']
                arc_user.arc_state = data['userState']
                arc_user.datawarehouse_sync = False
                arc_user.save()
                process = True

                event.processed = process

            event.save()
