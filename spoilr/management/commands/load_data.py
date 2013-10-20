from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from spoilr.load_data import load_all

class Command(BaseCommand):
    help = """Imports hunt models from text files.
"""

    def handle(self, *args, **options):
        load_all()
