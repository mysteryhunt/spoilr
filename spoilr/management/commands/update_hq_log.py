from django.core.management.base import BaseCommand
from spoilr.log import system_log_update

class Command(BaseCommand):
    help = """Generates the system log view.

This should be set to run every minute or so.
"""

    def handle(self, *args, **options):
        system_log_update()
