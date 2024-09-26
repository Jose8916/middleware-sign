import os
import sys
import time
from datetime import datetime

import pandas as pd
from apps.arcsubs.arcclient import ArcClientAPI  # arc identity/api
from apps.arcsubs.models import ArcUser  # middleware
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Arregla DisplayName basado en el uuid.",
        " Es decir, obtiene el profile por uuid",
        " se edita y finalmente se realiza el cambio"
    )

    def add_arguments(self, parser):

        # To run for one ser with uuid
        parser.add_argument(
            "--list_uuids",
            default=[],
            help=(
                "Envie la lista de uuids por este medio como el ejemplo:"
                " --list_uuid uuid1-uuid2-uuid3-uuid4,uuid5-uuid6-uuid7-uuid8"
                " \n Todo junto y separado por comas."
            ),
        )

    def handle(self, *args, **options):

        current_file = __file__.rsplit("/", 1)[1].split(".")[0]
        # max_iterations=100
        print(f"[{current_file}] Args: options:{options}")
        # parse parameters
        list_uuid = options["list_uuids"]

        try:
            client = ArcClientAPI()
            for user_uuid in  [item for item in list_uuid.split(',')]:
                print(f"user_uuid: {user_uuid}")
                profile = client.get_profile_by_uuid(user_uuid)
                local_uuid = profile["uuid"]
                response = client.update_DisplayName_in_Profile_by_uuid(
                    uuid=local_uuid, new_displayName=local_uuid,safe=True
                )
                for user in ArcUser.objects.filter(uuid=local_uuid):
                    local_user = user
                    print(f"Usuario encontrado con uuid={user.uuid}")

                local_user.profile["displayName"] = local_uuid
                local_user.display_name = local_uuid
                local_user.save()

        except Exception as e:
            print(f"[Exception] [{current_file}]: \t", e)

        finally:
            # change in local
            print(
                f"[Finish] [{current_file}]: \t",
                "Script finalizado y usuario actualizado.",
            )