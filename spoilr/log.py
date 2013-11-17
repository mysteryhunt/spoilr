from .models import *

PUZZLE_ACCESS = 'puzzle-access'
ROUND_ACCESS = 'round-access'
PUZZLE_SOLVED = 'puzzle-solved'
ROUND_SOLVED = 'round-solved'

def system_log(event_type, message, team=None, object_id=''):
    SystemLog.objects.create(event_type=event_type, message=message, team=team, object_id=object_id).save()

def team_log(team, event_type, message, object_id='', link=''):
    SystemLog.objects.create(event_type=event_type, message="Team Log: %s" % message, team=team, object_id=object_id).save()
    if team is None:
        return
    TeamLog.objects.create(event_type=event_type, message=message, team=team, object_id=object_id, link=link).save()

def team_log_round_access(team, round, reason):
    team_log(team, ROUND_ACCESS, 'Released round "%s" (%s)' % (round.name, reason), object_id=round.url, link="/round/%s" % round.url)

def team_log_puzzle_access(team, puzzle, reason):
    team_log(team, PUZZLE_ACCESS, 'Released puzzle "%s" (%s)' % (puzzle.name, reason), object_id=puzzle.url, link="/puzzle/%s" % puzzle.url)
