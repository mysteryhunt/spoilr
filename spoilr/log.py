from .models import *

PUZZLE_ACCESS = 'puzzle-access'
ROUND_ACCESS = 'round-access'
PUZZLE_SOLVED = 'puzzle-solved'
ROUND_SOLVED = 'round-solved'

def system_log(event_type, message, team=None, object_id=''):
    SystemLog.objects.create(event_type=event_type, message=message, team=team, object_id=object_id).save()

def team_log(team, event_type, message, object_id='', link=''):
    SystemLog.objects.create(event_type=event_type, message="Team Log: %s" % message, team=team, object_id=object_id).save()
    TeamLog.objects.create(event_type=event_type, message=message, team=team, object_id=object_id, link=link).save()
