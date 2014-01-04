from django.http import HttpResponse
from django.template import Context, loader
from django.core.cache import cache

from .models import *
from .constants import *

def TeamDict(team, puzzle_objects, puzzle_access, round_objects, round_access):
    logn = TeamLog.objects.filter(team=team).order_by('-timestamp')[:10]
    log1 = logn[0]
    p_released = sum(1 for a in puzzle_access if a.team == team)
    p_solved = sum(1 for a in puzzle_access if a.team == team and a.solved)
    q_submissions = sum(1 for a in PuzzleSubmission.objects.filter(team=team, resolved=False))
    q_submissions += sum(1 for a in MetapuzzleSubmission.objects.filter(team=team, resolved=False))
    q_submissions += sum(1 for a in Y2014MitMetapuzzleSubmission.objects.filter(team=team, resolved=False)) # 2014-specific
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
        for mitdata in Y2014MitPuzzleData.objects.all().order_by('id'):
            released = False
            solved = False
            access = [a for a in puzzle_access if a.team == team and a.puzzle == mitdata.puzzle]
            if len(access):
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
    for round in round_objects:
        if round.url == 'mit': # 2014-specific
            continue
        released = False
        solved = False
        access = [a for a in round_access if a.team == team and a.round == round]
        if len(access):
            released = True
            r_released += 1
            if MetapuzzleSolve.objects.filter(team=team, metapuzzle__url=round.url).exists():
                solved = True
                r_solved += 1
        rounds[round.url] = {'puzzles': [], 'released': released, 'solved': solved}
        for puzzle in (p for p in puzzle_objects if p.round == round):
            released = False
            solved = False
            access = [a for a in puzzle_access if a.team == team and a.puzzle == puzzle]
            if len(access):
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
        'p_open': p_released - p_solved,
        'q_submissions': q_submissions,
        }

def all_teams_update():
    print("updating all teams dashboard...")
    template = loader.get_template('all-teams.html') 
    teams = []
    for team in Team.objects.all():
        teams.append(TeamDict(team, Puzzle.objects.all(), PuzzleAccess.objects.all(), Round.objects.all(), RoundAccess.objects.all()))
    teams.sort(key=lambda team: -(team['r_solved'] * 5)-team['p_solved'])
    q_total = PuzzleSubmission.objects.filter(resolved=False).count()
    q_total += MetapuzzleSubmission.objects.filter(resolved=False).count()
    q_total += Y2014MitMetapuzzleSubmission.objects.filter(resolved=False).count() # 2014-specific
    q_teams = set()
    for x in PuzzleSubmission.objects.filter(resolved=False):
        q_teams.add(x.team.url)
    for x in MetapuzzleSubmission.objects.filter(resolved=False):
        q_teams.add(x.team.url)
    for x in Y2014MitMetapuzzleSubmission.objects.filter(resolved=False): # 2014-specific
        q_teams.add(x.team.url)
    s_total = MAX_POINTS # 2014-specific
    p_total = Puzzle.objects.count()
    r_total = Round.objects.count()
    r_total = r_total - 1 + 3 # 2014-specific
    context = Context({
        'teams': teams,
        'q_total': q_total,
        'q_teams': len(q_teams),
        's_total': s_total, # 2014-specific
        'r_total': r_total,
        'p_total': p_total,
    })
    cache.set('all_teams', template.render(context), None)
    print("...done")

def all_teams_view(request):
    return HttpResponse(cache.get('all_teams'))
