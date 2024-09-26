import os
import sys
import time
from datetime import datetime

import pandas as pd
from apps.arcsubs.arcclient import ArcClientAPI  # arc identity/api
from apps.arcsubs.models import ArcUser  # middleware
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.aggregates import Count


class Command(BaseCommand):
    help = (
        "Arregla DisplayName reemplazando el valor con el",
        " email guardado en ARC. Obtiene el email del middleware y guarda",
        " datos en ARC.",
        " Ejemplo de uso: python manage.py fix_displayname_allusers",
    )

    def add_arguments(self, parser):

        # To run for one ser with uuid
        parser.add_argument(
            "--one_uuid",
            default="",
            help=(
                "Use este comando para correr el script"
                " para un solo usuario."
                " El usuario tiene que estar en"
                " la lista filtrada para evitar errores."
            ),
        )

        parser.add_argument(
            "--max_iterations",
            default=100,
            help=("Número de máximas iteraciones. Default=100",),
        )

        parser.add_argument(
            "--only_duplicated",
            default="False",
            help=("Solo correr para duplicados. Default=False",),
        )

    def handle(self, *args, **options):

        users_completed = 0
        user_failed = 0
        users_completed_local = 0
        current_file = __file__.rsplit("/", 1)[1].split(".")[0]
        # max_iterations=100
        print(f"[{current_file}] Args: options:{options}")
        # parse parameters
        one_uuid = str(options["one_uuid"])
        max_iterations = int(options["max_iterations"])
        only_duplicated = options["only_duplicated"]

        uuid_list = []
        fecha_list = []
        email_list = []
        displayName_list = []
        displayName_fixed_list = []
        corregido_list = []
        duplicado_list = []

        if one_uuid:
            # with one uuid
            print(f"[{current_file}] Modo solo un usuario por uuid.")
            try:
                client = ArcClientAPI()
                profile = client.get_profile_by_uuid(one_uuid)
                local_uuid = profile["uuid"]
                local_email = str(profile["email"])
                response = client.update_DisplayName_in_Profile_by_uuid(
                    uuid=local_uuid, new_displayName=local_email
                )
                local_user = None
                for user in ArcUser.objects.filter(uuid=one_uuid):
                    local_user = user
                    print(f"Usuario encontrado con uuid={user.uuid}")

                local_user.profile["displayName"] = local_email
                local_user.display_name = local_email
                local_user.save()

            except Exception as e:
                print(f"[Exception] [{current_file}]: \t", e)
            finally:
                # change in local
                print(
                    f"[Finish] [{current_file}]: \t",
                    "Script finalizado y usuario actualizado.",
                )
        else:
            print(f"[{current_file}] Modo iteraciones.")

            if only_duplicated == "True":
                # SOLO PARA USUARIOS CON DISPLAYNAME DUPLICADOS
                print(f"[{current_file}] only_duplicated True")
                list_arc_filtered = (
                    ArcUser.objects.filter(Q(profile__status__contains="Active"))
                    .exclude(
                        Q(display_name__contains="@")
                        | Q(display_name="")
                        | Q(display_name__isnull=True)
                        | Q(first_login_method__contains="Facebook")
                        | Q(deletedusers__status="Ready")
                        | Q(requestdeletes__status="PendingApproval")
                    )
                    .order_by("display_name")
                )

                duplicates = (
                    list_arc_filtered.values("display_name")
                    .annotate(Count("display_name"))
                    .filter(display_name__count__gt=1)
                    .order_by("display_name")
                )
                users = (
                    ArcUser.objects.filter(
                        display_name__in=[item["display_name"] for item in duplicates]
                    )
                    .exclude(
                        Q(display_name__contains="@")
                        | Q(display_name="")
                        | Q(display_name__isnull=True)
                        | Q(first_login_method__contains="Facebook")
                        | Q(deletedusers__status="Ready")
                        | Q(requestdeletes__status="PendingApproval")
                    )
                    .order_by("display_name")
                )

            elif only_duplicated == "False":
                # PARA USUARIOS CON EL ERROR POTENCIAL
                print(f"[{current_file}] only_duplicated False")
                users = (
                    ArcUser.objects.filter(Q(profile__status__contains="Active"))
                    .exclude(
                        Q(display_name__contains="@")
                        | Q(display_name="")
                        | Q(display_name__isnull=True)
                        | Q(first_login_method__contains="Facebook")
                        | Q(deletedusers__status="Ready")
                        | Q(requestdeletes__status="PendingApproval")
                    )
                    .order_by("display_name")
                )

            print(f"[{current_file}] [QUERY] {users.query}")

            print(
                f"[{current_file}] Hay {len(users)} usuario(s) detectado(s) con el patrón que genera errores"
            )
            for user in users.iterator():
                # Avoid saturation of API
                time.sleep(0.05)  # 50 ms
                if users_completed + user_failed >= max_iterations:
                    print(
                        f"[{current_file}] Iteración interrumpida"
                        " adrede para evitar errores."
                        " Sin embargo, los iterados ya fuerona"
                        " afectados por el script"
                    )
                    break

                # get email from middleware and store in local dict
                local_uuid = str(user.uuid)

                # Depens where is the email
                try:
                    local_email = str(user.profile.get("email"))
                except Exception:
                    local_email = str(user.email)

                print(
                    f"[{current_file}] -MIDDLEWARE-",
                    user.uuid,
                    user.email,
                    "-ARC-",
                    local_email,
                )

                # save on displayName
                try:
                    client = ArcClientAPI()
                    response = client.update_DisplayName_in_Profile_by_uuid(
                        uuid=local_uuid, new_displayName=local_email
                    )
                    if response.status_code == 200:
                        users_completed += 1
                        completado = True

                    else:
                        user_failed += 1
                        completado = False

                    print(str(user.uuid), "replaced displayName with", str(local_email))

                except Exception as e:
                    user_failed += 1
                    print(f"[Exception] [{current_file}]: \t", e)
                    completado = f"Exception {e}"
                finally:
                    # Dataframe: collect data
                    uuid_list.append(local_uuid)
                    fecha_list.append(datetime.today())
                    email_list.append(local_email)
                    displayName_list.append(user.profile["displayName"])
                    displayName_fixed_list.append(local_email)
                    corregido_list.append(completado)
                    duplicado_list.append(only_duplicated)

                    # change in local
                    user.profile["displayName"] = local_email
                    user.display_name = local_email
                    user.save()
                    users_completed_local += 1

            print(
                f"[{current_file}] Users completed [ARC]: {users_completed} \
                    Users failed [ARC]: {user_failed}\
                    Users completed in local: {users_completed_local}"
            )

            print(f"[{current_file}] DATAFRAME-------------------------------------")

            with pd.option_context(
                "display.max_rows", None, "display.max_columns", None
            ):  # Print in console without restrictions of rows and columns

                df = pd.DataFrame(
                    {
                        "uuid": uuid_list,
                        "fecha": fecha_list,
                        "email": email_list,
                        "displayName_antes": displayName_list,
                        "displayName_despues": displayName_fixed_list,
                        "corregido": corregido_list,
                        "duplicado": duplicado_list,
                    }
                )
                # Imprimir en consola resultados
                print(df.to_csv())

                # Guardar en csv local
                df.to_csv("fix_displayname_allusers.csv", sep=";", index=False)

            print(f"[{current_file}] FINISH-------------------------------------")
