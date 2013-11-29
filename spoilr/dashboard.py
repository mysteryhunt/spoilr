from django.http import HttpResponse
from django.template import RequestContext, loader

from .models import *

def TeamSections(team): # 2014-specific
    sections = []
    dormouse_puzzles = []
    caterpillar_puzzles = []
    tweedle_puzzles = []
    for mitdata in Y2014MitPuzzleData.objects.all():
        released = False
        solved = False
        access = PuzzleAccess.objects.filter(team=team, puzzle=mitdata.puzzle)
        if access.exists():
            released = True
            if access[0].solved:
                solved = True
        p = {
            'puzzle': mitdata.puzzle,
            'released': released,
            'solved': solved,
            }
        if mitdata.mit_meta() == 'dormouse':
            dormouse_puzzles.append(p)
        if mitdata.mit_meta() == 'caterpillar':
            caterpillar_puzzles.append(p)
        if mitdata.mit_meta() == 'tweedle':
            tweedle_puzzles.append(p)
    sections.append({'puzzles': dormouse_puzzles, 'released': True, 'solved': MetapuzzleSolve.objects.filter(team=team, metapuzzle__name='The Dormouse').exists()})
    sections.append({'puzzles': caterpillar_puzzles, 'released': True, 'solved': MetapuzzleSolve.objects.filter(team=team, metapuzzle__name='The Caterpillar').exists()})
    sections.append({'puzzles': tweedle_puzzles, 'released': True, 'solved': MetapuzzleSolve.objects.filter(team=team, metapuzzle__name='Tweedledee and Tweedledum').exists()})
    return sections

def TeamDict(team):
    logn = list(reversed(TeamLog.objects.filter(team=team).order_by('-timestamp')[:5]))
    log1 = logn[-1]
    return {
        'team': team,
        'logn': logn,
        'log1': log1,
        'sections': TeamSections(team)
        }

def all_teams(request):
    template = loader.get_template('all-teams.html') 
    puzzle_count = Puzzle.objects.all().count()
    teams = []
    for team in Team.objects.all():
        teams.append(TeamDict(team))
    context = RequestContext(request, {
            'teams': teams,
            'puzzle_count': puzzle_count,
            })
    return HttpResponse(template.render(context))
