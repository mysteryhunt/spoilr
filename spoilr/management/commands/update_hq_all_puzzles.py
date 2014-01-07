from django.core.management.base import BaseCommand
from spoilr.dashboard import all_puzzles_update

class Command(BaseCommand):
    help = """Generates the all puzzles dashboard.

This should be set to run every ten minutes or so.
"""

    def handle(self, *args, **options):
        all_puzzles_update()
