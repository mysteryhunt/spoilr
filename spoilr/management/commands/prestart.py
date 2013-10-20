from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from spoilr.publish import prestart_all

class Command(BaseCommand):
    help = """Prestarts the hunt.

For each team:
  - create team directory if not already present
"""

# TODO: htaccess files?
# TODO: countdown page?
# (https://github.com/mysteryhunt/huntrunning/blob/master/solving/management/commands/prestart.py)

    def handle(self, *args, **options):
        prestart_all()
