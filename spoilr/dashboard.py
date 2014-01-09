from django.http import HttpResponse
from django.template import Context, loader
from django.core.cache import cache
from django.db.models import Q

from .models import *
from .constants import *

def TeamDict(team):
    logn = TeamLog.objects.filter(team=team).order_by('-timestamp')[:10]
    log1 = logn[0]
    p_released = PuzzleAccess.objects.filter(team=team).count()
    p_solved = PuzzleAccess.objects.filter(team=team, solved=True).count()
    q_submissions = PuzzleSubmission.objects.filter(team=team, resolved=False).count()
    q_submissions += MetapuzzleSubmission.objects.filter(team=team, resolved=False).count()
    q_submissions += Y2014MitMetapuzzleSubmission.objects.filter(team=team, resolved=False).count() # 2014-specific
    q_submissions += ContactRequest.objects.filter(team=team, resolved=False).count()
    q_submissions += Y2014PwaGarciaparraUrlSubmission.objects.filter(team=team, resolved=False).count() # 2014-specific
    rounds = dict()
    if True: # 2014-specific
        s_current = Y2014TeamData.objects.get(team=team).points
        r_released = 3
        r_solved = 0
        for x in ['spades', 'clubs', 'diamonds']:
            solved = MetapuzzleSolve.objects.filter(team=team, metapuzzle__url=x).exists()
            if solved:
                r_solved += 1
            rounds[x] = {'puzzles': [], 'released': True, 'solved': solved}
        for mitdata in Y2014MitPuzzleData.objects.all().order_by('id'):
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
            if mitdata.mit_meta() == 'spades':
                rounds['spades']['puzzles'].append(p)
            elif mitdata.mit_meta() == 'clubs':
                rounds['clubs']['puzzles'].append(p)
            elif mitdata.mit_meta() == 'diamonds':
                rounds['diamonds']['puzzles'].append(p)
    for round in Round.objects.all():
        if round.url == 'mit': # 2014-specific
            continue
        released = False
        solved = False
        access = RoundAccess.objects.filter(team=team,round=round)
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
        'p_open': p_released - p_solved,
        'q_submissions': q_submissions,
        }

def all_teams_update():
    print("updating all teams dashboard...")
    template = loader.get_template('all-teams.html') 
    teams = []
    for team in Team.objects.filter(~Q(url='hunt_hq')):
        teams.append(TeamDict(team))
    teams.sort(key=lambda team: -(team['r_solved'] * 5)-team['p_solved'])
    f = ~Q(team__url='hunt_hq') & Q(resolved=False)
    q_total = PuzzleSubmission.objects.filter(f).count()
    q_total += MetapuzzleSubmission.objects.filter(f).count()
    q_total += Y2014MitMetapuzzleSubmission.objects.filter(f).count() # 2014-specific
    q_teams = set()
    for x in PuzzleSubmission.objects.filter(f):
        q_teams.add(x.team.url)
    for x in MetapuzzleSubmission.objects.filter(f):
        q_teams.add(x.team.url)
    for x in Y2014MitMetapuzzleSubmission.objects.filter(f): # 2014-specific
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
    cache.set('all_teams', template.render(context), 60*60)
    print("...done")

def all_teams_view(request):
    return HttpResponse(cache.get('all_teams'))

def all_puzzles_update():
    print("updating all puzzles dashboard...")
    template = loader.get_template('all-puzzles.html') 
    t_total = Team.objects.filter(~Q(url='hunt_hq')).count()

    def percent(n, d):
        if d == 0 or d < 3:
            return '-'
        return int(n*100/d)

    metas = []
    for mm in ['spades', 'clubs', 'diamonds']: # 2014-specific
        meta = Metapuzzle.objects.get(url=mm)
        released = t_total
        solved = MetapuzzleSolve.objects.filter(~Q(team__url='hunt_hq') & Q(metapuzzle=meta)).count()
        puzzles = []

        m = {
            'meta': meta,
            'puzzles': puzzles,
            'released': released,
            'releasedp': percent(released, t_total),
            'solved': solved,
            'solvedp': percent(solved, released),
        }
        metas.append(m)
    for mitdata in Y2014MitPuzzleData.objects.all().order_by('id'): # 2014-specific
        released = PuzzleAccess.objects.filter(~Q(team__url='hunt_hq') & Q(puzzle=mitdata.puzzle)).count()
        solved = PuzzleAccess.objects.filter(~Q(team__url='hunt_hq') & Q(puzzle=mitdata.puzzle) & Q(solved=True)).count()
        p = {
            'puzzle': mitdata.puzzle,
            'info': mitdata.card.name,
            'released': released,
            'releasedp': percent(released, t_total),
            'solved': solved,
            'solvedp': percent(solved, released),
        }
        if mitdata.mit_meta() == 'spades':
            metas[0]['puzzles'].append(p)
        elif mitdata.mit_meta() == 'clubs':
            metas[1]['puzzles'].append(p)
        elif mitdata.mit_meta() == 'diamonds':
            metas[2]['puzzles'].append(p)
    for round in Round.objects.all().order_by('id'):
        if round.url == 'mit': # 2014-specific
            continue
        meta = Metapuzzle.objects.get(url=round.url)
        puzzles = []
        for puzzle in Puzzle.objects.filter(round=round).order_by('id'):
            released = PuzzleAccess.objects.filter(~Q(team__url='hunt_hq') & Q(puzzle=puzzle)).count()
            solved = PuzzleAccess.objects.filter(~Q(team__url='hunt_hq') & Q(puzzle=puzzle) & Q(solved=True)).count()
            info = ''
            if round.url == 'tea_party':
                rounddata = Y2014PartyAnswerData.objects.get(answer=puzzle.answer)
                if rounddata.type1 == 'chair':
                    info = rounddata.type1+' ('+rounddata.type2+')'
                else:
                    info = rounddata.type1+' ('+rounddata.type2+', '+str(rounddata.level)+')'
            if round.url == 'caucus_race':
                rounddata = Y2014CaucusAnswerData.objects.filter(yes_answer=puzzle.answer)
                if rounddata.exists():
                    info = '%d YES' % rounddata[0].bird
                else:
                    rounddata = Y2014CaucusAnswerData.objects.filter(no_answer=puzzle.answer)
                    if rounddata.exists():
                        info = '%d NO' % rounddata[0].bird
            if round.url == 'knights':
                rounddata = Y2014KnightsAnswerData.objects.get(answer=puzzle.answer)
                info = '%s %s' % (rounddata.color, rounddata.piece)
            p = {
                'puzzle': puzzle,
                'info': info,
                'released': released,
                'releasedp': percent(released, t_total),
                'solved': solved,
                'solvedp': percent(solved, released),
            }
            puzzles.append(p)
        released = RoundAccess.objects.filter(~Q(team__url='hunt_hq') & Q(round=round)).count()
        solved = MetapuzzleSolve.objects.filter(~Q(team__url='hunt_hq') & Q(metapuzzle=meta)).count()
        m = {
            'meta': meta,
            'puzzles': puzzles,
            'released': released,
            'releasedp': percent(released, t_total),
            'solved': solved,
            'solvedp': percent(solved, released),
        }
        metas.append(m)
    p_total = Puzzle.objects.count()
    context = Context({
        'metas': metas,
        't_total': t_total,
        'p_total': p_total,
    })
    cache.set('all_puzzles', template.render(context), 60*60)
    print("...done")

def all_puzzles_view(request):
    return HttpResponse(cache.get('all_puzzles'))
