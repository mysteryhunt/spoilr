from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from spoilr.publish import start_all, publish_all

class Command(BaseCommand):
    help = """Starts the hunt.

For each team:
  - give team access to initial round and puzzle set
For each team:
  - publish team directory
"""

# TODO: htaccess files?
# TODO: countdown page?
# (https://github.com/mysteryhunt/huntrunning/blob/master/solving/management/commands/prestart.py)

    def handle(self, *args, **options):
        start_all()
        publish_all()
