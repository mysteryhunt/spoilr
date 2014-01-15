from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from spoilr.publish import republish_all

class Command(BaseCommand):
    help = """Republishes all team directories.

This might be useful for cleaning up after making database changes.

For each team:
  - republish team directory
"""

# TODO: htaccess files?
# TODO: countdown page?
# (https://github.com/mysteryhunt/huntrunning/blob/master/solving/management/commands/prestart.py)

    def handle(self, *args, **options):
        republish_all()
