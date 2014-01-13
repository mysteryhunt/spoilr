from django.http import HttpResponse
from django.template import Context, loader
from django.core.cache import cache

from .models import *

import logging
logger = logging.getLogger(__name__)

PUZZLE_ACCESS = 'puzzle-access'
ROUND_ACCESS = 'round-access'
PUZZLE_SOLVED = 'puzzle-solved'
PUZZLE_INCORRECT = 'puzzle-incorrect'
METAPUZZLE_SOLVED = 'metapuzzle-solved'
METAPUZZLE_INCORRECT = 'metapuzzle-incorrect'
INTERACTION = 'interaction'

def system_log(event_type, message, team=None, object_id=''):
    logger.debug('Hunt System Log: type=%s message=\'%s\' team=%s object=%s', event_type, message, team, object_id)
    SystemLog.objects.create(event_type=event_type, message=message, team=team, object_id=object_id).save()

def team_log(team, event_type, message, object_id='', link=''):
    SystemLog.objects.create(event_type=event_type, message="Team Log: %s" % message, team=team, object_id=object_id).save()
    if team is None:
        return
    TeamLog.objects.create(event_type=event_type, message=message, team=team, object_id=object_id, link=link).save()

def team_log_round_access(team, round, reason):
    team_log(team, ROUND_ACCESS, 'Released round "%s" (%s)' % (round.name, reason), object_id=round.url, link="/round/%s/" % round.url)

def team_log_puzzle_access(team, puzzle, reason):
    team_log(team, PUZZLE_ACCESS, 'Released puzzle "%s" (%s)' % (puzzle.name, reason), object_id=puzzle.url, link="/puzzle/%s/" % puzzle.url)

def team_log_interaction_access(team, interaction, reason):
    team_log(team, INTERACTION, 'Ready for interaction "%s" (%s)' % (interaction.name, reason), object_id=interaction.url)

def team_log_puzzle_solved(team, puzzle):
    team_log(team, PUZZLE_SOLVED, 'Solved puzzle "%s"' % puzzle.name, object_id=puzzle.url, link="/puzzle/%s" % puzzle.url)

def team_log_puzzle_incorrect(team, puzzle, answer):
    system_log(PUZZLE_INCORRECT, 'Incorrect answer "[[%s]]" for puzzle "%s"' % (answer, puzzle.name), team=team, object_id=puzzle.url)

def team_log_metapuzzle_solved(team, metapuzzle):
    team_log(team, METAPUZZLE_SOLVED, 'Solved metapuzzle "%s"' % metapuzzle.name, object_id=metapuzzle.url)

def team_log_metapuzzle_incorrect(team, metapuzzle, answer):
    system_log(METAPUZZLE_INCORRECT, 'Incorrect answer "[[%s]]" for metapuzzle "%s"' % (answer, metapuzzle.name), team=team, object_id=metapuzzle.url)

def team_log_mit_meta_incorrect(team, answer):
    system_log(METAPUZZLE_INCORRECT, 'Incorrect mit submission "[[%s]]"' % answer, team=team)

def team_log_interaction_accomplished(team, interaction):
    team_log(team, INTERACTION, 'Accomplished interaction "%s"' % interaction.name, object_id=interaction.url)

def team_log_hole_discovered_no_vial(team):
    team_log(team, 'story', 'You found a small hole, but you don\'t yet have enough drink-me potion to jump in there.')

def team_log_vial_filled_no_hole(team):
    team_log(team, 'story', 'You filled a vial of drink-me potion, but you haven\'t found any small holes to jump into.')

def system_log_update():
    print("updating system log view...")
    entries = SystemLog.objects.all().order_by('-id')
    template = loader.get_template('log.html') 
    context = Context({
        'entries': entries,
    })
    cache.set('system_log', template.render(context), 60*60)
    print("...done")

def system_log_view(request):
    return HttpResponse(cache.get('system_log'))
