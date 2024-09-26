from django.core.management.base import BaseCommand
from apps.arcsubs.models import PromotionUser, ArcUser


class Command(BaseCommand):
    help = 'comando que actualiza la realacion con arc_user'

    def handle(self, *args, **options):
        promotion_user = PromotionUser.objects.filter(arc_user__isnull=True)
        for user in promotion_user:
            try:
                arc_user = ArcUser.objects.get(uuid=user.uuid)
            except Exception:
                arc_user = ''

            if arc_user:
                PromotionUser.objects.filter(uuid=user.uuid).update(arc_user=arc_user)


