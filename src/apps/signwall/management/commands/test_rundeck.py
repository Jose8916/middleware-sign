from django.core.management.base import BaseCommand
from django.db.models import Q
import random


class Command(BaseCommand):
    help = (
        "Comando para probar en Rundeck que ",
        "imprime 10 números y luego levanta un error",
    )

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            "--iterations",
            # action='store',
            help="Change number of iterations",
        )

    def handle(self, *args, **options):

        current_file = __file__.rsplit("/", 1)[1].split(".")[0]

        # get arguments
        max_iters = 10
        if options["iterations"]:
            max_iters = int(options["iterations"])
        print(f"[{current_file}] max_iters: {options['iterations']}")
        for i in range(max_iters):
            print(f"[{current_file}] Iteración {i}:\t{random.randint(0,10)}")
