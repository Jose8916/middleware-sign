from .models import ArcEvent, ArcUser
from .arcclient import ArcClientAPI


def load_user(event):
    client = ArcClientAPI()
    defaults = {}
    uuid = event.message.get('uuid')
    if event.message.get('email'):
        defaults['email'] = event.message.get('email')

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


def send_verify_email(event):
    uuid = event.message.get('uuid')
    user = ArcUser.objects.get(uuid=uuid)
    context = {}
    context.update(event.message)
    context.update(user.profile)


def process_event(event_id):
    event = ArcEvent.objects.get(id=event_id)

    if not event.processed:
        pipelines = EVENT_TYPE_PIPELINES.get(event.event_type, [])
        try:
            for pipeline in pipelines:
                pipeline(event)

        except Exception:
            print("Error process_event")

        else:
            event.processed = True
            event.save()


EVENT_TYPE_PIPELINES = {
    'SIGNUP_EDIT': [
        load_user,
        send_verify_email,
    ],
    'PROFILE_EDIT': [
        load_user,
    ],
}
