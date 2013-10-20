from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from spoilr.load_data import everybody_can_see_everything

class Command(BaseCommand):
    help = """Removes all teams, rounds and puzzles from the database.
"""

    def handle(self, *args, **options):
        everybody_can_see_everything()
