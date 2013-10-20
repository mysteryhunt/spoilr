from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from spoilr.load_data import wipe_database_i_really_mean_it

class Command(BaseCommand):
    help = """Removes all teams, rounds and puzzles from the database.
"""

    def handle(self, *args, **options):
        wipe_database_i_really_mean_it()
