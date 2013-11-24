from .models import *

PUZZLE_ACCESS = 'puzzle-access'
ROUND_ACCESS = 'round-access'
PUZZLE_SOLVED = 'puzzle-solved'
PUZZLE_INCORRECT = 'puzzle-incorrect'
METAPUZZLE_SOLVED = 'metapuzzle-solved'
METAPUZZLE_INCORRECT = 'metapuzzle-incorrect'

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

def team_log_puzzle_solved(team, puzzle):
    team_log(team, PUZZLE_SOLVED, 'Solved puzzle "%s" (answer "[[%s]]")' % (puzzle.name, puzzle.answer), object_id=puzzle.url, link="/puzzle/%s" % puzzle.url)

def team_log_puzzle_incorrect(team, puzzle, answer):
    team_log(team, PUZZLE_INCORRECT, 'Incorrect answer "[[%s]]" for puzzle "%s"' % (answer, puzzle.name), object_id=puzzle.url)

def team_log_metapuzzle_solved(team, metapuzzle):
    team_log(team, METAPUZZLE_SOLVED, 'Solved metapuzzle "%s" (answer "[[%s]]")' % (metapuzzle.name, metapuzzle.answer), object_id=metapuzzle.name)

def team_log_metapuzzle_incorrect(team, metapuzzle, answer):
    team_log(team, METAPUZZLE_INCORRECT, 'Incorrect answer "[[%s]]" for metapuzzle "%s"' % (answer, metapuzzle.name), object_id=metapuzzle.name)
