# from sentry_sdk import capture_message
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.arcsubs.models import ArcUser
from apps.arcsubs.utils import timestamp_to_datetime


class Command(BaseCommand):
    help = 'Completa el campo first_site de los usuarios.'

    def add_arguments(self, parser):
        parser.add_argument('--update_first_site', nargs='?', type=str)
        parser.add_argument('--update_created_on', nargs='?', type=str)

    def handle(self, *args, **options):

        if options.get('update_created_on'):
            queryset_base = ArcUser.objects.filter(created_on__isnull=True)
            print("> 1. Existen {} usuarios sin created_on".format(queryset_base.count(), ))
            for user in queryset_base.iterator():
                if user.profile.get('createdOn', ''):
                    ArcUser.objects.filter(uuid=user.uuid).update(
                        created_on=timestamp_to_datetime(user.profile['createdOn'])
                    )
                """
                else:
                    for identity in user.identities:
                        if identity.get('createdOn', ''):
                            user.update(created_on=timestamp_to_datetime(identity['createdOn']))
                """
            print("> 2. Quedan {} usuarios sin created_on".format(queryset_base.count(), ))

        if options.get('update_first_site'):
            last_updated = timezone.now()
            print("> {}".format(last_updated))

            without_first_site = ArcUser.objects.filter(first_site__isnull=True).count()
            print("> 1. Existen {} usuarios sin first_site".format(without_first_site))

            ArcUser.objects.filter(
                first_site__isnull=True
            ).update(
                first_site='elcomercio',
                last_updated=last_updated
            )
            without_first_site = ArcUser.objects.filter(first_site__isnull=True).count()
            print("> 2. Existen {} usuarios sin first_site".format(without_first_site))


            # queryset_base = ArcUser.objects.filter(first_site__isnull=True)
            # # last_updated = timezone.now()

            # print("> Quedan {} usuarios sin first_site".format(queryset_base.count(), ))
            # # print("> {}".format(last_updated))
            # count = 0
            # for user in queryset_base.iterator():
            #     user.first_site = 'elcomercio'
            #     user.save()
            #     count = count + 1

            # #     user.update_arc_profile(commit=False)
            # #     user.load_first_login(commit=False)
            # #     user.last_updated = last_updated
            # #     user.save()

            # capture_message("Se ejecutarion {} registros".format(count, ))
