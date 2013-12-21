from django.http import HttpResponse
from django.template import RequestContext, loader

from .models import *
from .constants import *

def TeamMitData(team): # 2014-specific
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
    data = dict()
    data["dormouse"] = {'puzzles': dormouse_puzzles, 'released': True, 'solved': MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='dormouse').exists()}
    data["caterpillar"] = {'puzzles': caterpillar_puzzles, 'released': True, 'solved': MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='caterpillar').exists()}
    data["tweedles"] = {'puzzles': tweedle_puzzles, 'released': True, 'solved': MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='tweedles').exists()}
    return data

def TeamDict(team):
    logn = TeamLog.objects.filter(team=team).order_by('-timestamp')[:10]
    log1 = logn[0]
    p_released = PuzzleAccess.objects.filter(team=team).count()
    p_solved = PuzzleAccess.objects.filter(team=team, solved=True).count()
    rounds = dict()
    if True: # 2014-specific
        s_current = Y2014TeamData.objects.get(team=team).points
        r_released = 3
        r_solved = 0
        for x in ['dormouse', 'caterpillar', 'tweedles']:
            solved = MetapuzzleSolve.objects.filter(team=team, metapuzzle__url=x).exists()
            if solved:
                r_solved += 1
            rounds[x] = {'puzzles': [], 'released': True, 'solved': solved}
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
                rounds['dormouse']['puzzles'].append(p)
            elif mitdata.mit_meta() == 'caterpillar':
                rounds['caterpillar']['puzzles'].append(p)
            elif mitdata.mit_meta() == 'tweedles':
                rounds['tweedles']['puzzles'].append(p)
    for round in Round.objects.all():
        if round.url == 'mit': # 2014-specific
            continue
        released = False
        solved = False
        access = RoundAccess.objects.filter(team=team, round=round)
        if access.exists():
            released = True
            r_released += 1
            if MetapuzzleSolve.objects.filter(team=team, metapuzzle__url=round.url).exists():
                solved = True
                r_solved += 1
        rounds[round.url] = {'puzzles': [], 'released': released, 'solved': solved}
        for puzzle in Puzzle.objects.filter(round=round):
            released = False
            solved = False
            access = PuzzleAccess.objects.filter(team=team, puzzle=puzzle)
            if access.exists():
                released = True
                if access[0].solved:
                    solved = True
            p = {
                'puzzle': puzzle,
                'released': released,
                'solved': solved,
            }
            rounds[round.url]['puzzles'].append(p)
    return {
        'team': team,
        'rounds': rounds,
        'logn': logn,
        'log1': log1,
        's_current': s_current, # 2014-specific
        'r_released': r_released,
        'r_solved': r_solved,
        'p_released': p_released,
        'p_solved': p_solved,
        }

def all_teams(request):
    template = loader.get_template('all-teams.html') 
    teams = []
    for team in Team.objects.all():
        teams.append(TeamDict(team))
    teams.sort(key=lambda team: -(team['r_solved'] * 5)-team['p_solved'])
    s_total = MAX_POINTS # 2014-specific
    p_total = Puzzle.objects.count()
    r_total = Round.objects.count()
    r_total = r_total - 1 + 3 # 2014-specific
    context = RequestContext(request, {
        'teams': teams,
        's_total': s_total, # 2014-specific
        'r_total': r_total,
        'p_total': p_total,
    })
    return HttpResponse(template.render(context))
