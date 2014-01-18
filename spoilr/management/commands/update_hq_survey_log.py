from django.core.management.base import BaseCommand
from spoilr.survey_log import survey_log_update

class Command(BaseCommand):
    help = """Generates the survey log view.

This should be set to run every minute or so.
"""

    def handle(self, *args, **options):
        survey_log_update()
