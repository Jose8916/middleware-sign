from django.core.management.base import BaseCommand

from django.conf import settings

from ...models import ArcEvent, ArcUser, MailTemplate, SendMail
from ...arcclient import ArcClientAPI


class Command(BaseCommand):
    help = 'Ejecuta el comando'

    def handle(self, *args, **options):
        events = ArcEvent.objects.filter(
            processed=False,
            event_type__in=('SIGNUP_EDIT', 'PROFILE_EDIT', 'PASSWORD_RESET_REQUEST')
        )[:10]
        client = ArcClientAPI()

        urlSite = settings.CONFIG['elcomercio']['url']

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

            if event.event_type:
                try:
                    mail_template = MailTemplate.objects.get(state=True, event_type=event.event_type)
                    message = event.message
                    if event.event_type == 'SIGNUP_EDIT':
                        params = {
                            'name': data['profile']['displayName'],
                            'url': urlSite + '/register/validate'
                        }
                    elif event.event_type == 'PASSWORD_RESET_REQUEST':
                        params = {
                            'name': data['profile']['displayName'],
                            'url': urlSite + '?tokenReset=' + message['nonce']
                        }

                    SendMail.objects.create(
                        email=data['profile']['email'],
                        data=params,
                        mail_template_id=mail_template.id
                    )
                    process = True

                except Exception as e:
                    print(e)
                    print(event.id)
                    process = False
                    pass

            event.processed = process
            event.save()
