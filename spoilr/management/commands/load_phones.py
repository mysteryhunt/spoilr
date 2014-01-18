from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from spoilr.load_data import load_team_phones

class Command(BaseCommand):
    help = """Imports team phone numbers from text files.
"""

    def handle(self, *args, **options):
        load_team_phones()
