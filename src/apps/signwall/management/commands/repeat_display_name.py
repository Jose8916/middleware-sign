import pytz
import time
import csv
from django.core.management.base import BaseCommand
from apps.arcsubs.models import ArcUser, DeletedUser
TIMEZONE = pytz.timezone('America/Lima')


class Command(BaseCommand):
    help = 'Actualiza data de usuarios migrados de MPP a ARC Publishing'

    def add_arguments(self, parser):
        parser.add_argument('--displayname', nargs='?', type=str)
        parser.add_argument('--deleted', nargs='?', type=str)

    def handle(self, *args, **options):
        if options.get('displayname'):
            query_string = 'SELECT  1 as id , display_name, string_agg( to_char("created_on", \'DD/MM/YYYY HH12:MIPM\') || \' * \' || domain || \' * \' || email || \' * \' || uuid, \', \') as fecha_creacion, COUNT(display_name) as dcount FROM arcsubs_arcuser GROUP BY (display_name) HAVING (COUNT(display_name))>1'
            users = ArcUser.objects.raw(query_string)

            list_user = []
            for user in users:
                dict_user = {}
                tosplit = user.fecha_creacion
                if tosplit:
                    data_user = tosplit.split(',')
                else:
                    data_user = ''

                dict_user['display_name'] = user.display_name
                dict_user['dcount'] = user.dcount
                dict_user['data'] = data_user
                list_user.append(dict_user)

            nro = 0
            for user_obj in list_user:
                nro = nro + 1
                print(user_obj.get('display_name', '') + ' + ' + str(user_obj.get('data', '')))

            print('Total: ' + str(nro))

        if options.get('deleted'):
            delete_users = DeletedUser.objects.filter(status='Ready')

            with open('/tmp/reporte_eliminados.csv', 'a') as csvFile:
                writer = csv.writer(csvFile)

                for d in delete_users:
                    row = [d.arc_user.uuid]
                    writer.writerow(row)
                csvFile.close()
