from django.http import HttpResponse
from django.template import Context, loader
from django.core.cache import cache

from .models import *
from .constants import *

import logging
logger = logging.getLogger(__name__)

def TeamDict(team):
    logn = TeamLog.objects.filter(team=team).order_by('-timestamp')[:10]
    log1 = logn[0]
    p_released = PuzzleAccess.objects.filter(team=team).count()
    p_solved = PuzzleAccess.objects.filter(team=team, solved=True).count()
    p_surveyed = PuzzleSurvey.objects.filter(team=team).values('puzzle__url').distinct().count()
    q_submissions = PuzzleSubmission.objects.filter(team=team, resolved=False).count()
    q_submissions += MetapuzzleSubmission.objects.filter(team=team, resolved=False).count()
    q_submissions += Y2014MitMetapuzzleSubmission.objects.filter(team=team, resolved=False).count() # 2014-specific
    q_submissions += ContactRequest.objects.filter(team=team, resolved=False).count()
    q_submissions += Y2014PwaGarciaparraUrlSubmission.objects.filter(team=team, resolved=False).count() # 2014-specific
    rounds = dict()
    j_released = InteractionAccess.objects.filter(team=team, interaction__url='mit_runaround', accomplished=True).exists()
    j_solved = MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='jabberwock').exists()
    i_released = InteractionAccess.objects.filter(team=team).count()
    i_solved = InteractionAccess.objects.filter(team=team, accomplished=True).count()
    interactions = []
    for interaction in Interaction.objects.all().order_by('id'):
        released = False
        solved = False
        access = InteractionAccess.objects.filter(team=team, interaction=interaction)
        if access.exists():
            released = True
            if access[0].accomplished:
                solved = True
        i = {
            'interaction': interaction,
            'released': released,
            'solved': solved,
        }
        interactions.append(i)
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
    pwa_garciaparra_url = None # 2014-specific
    if InteractionAccess.objects.filter(team=team, interaction__url='pwa_garciaparra_url', accomplished=True).exists(): # 2014-specific
        try:
            pwa_garciaparra_url = Y2014PwaGarciaparraUrlSubmission.objects.filter(team=team).order_by('-id')[0].url
        except:
            pwa_garciaparra_url = '???'
    return {
        'team': team,
        'rounds': rounds,
        'interactions': interactions,
        'logn': logn,
        'log1': log1,
        's_current': s_current, # 2014-specific
        'j_released': j_released, # 2014-specific
        'j_solved': j_solved, # 2014-specific
        'r_released': r_released,
        'r_solved': r_solved,
        'p_released': p_released,
        'p_solved': p_solved,
        'p_open': p_released - p_solved,
        'p_surveyed': p_surveyed,
        'q_submissions': q_submissions,
        'i_released': i_released,
        'i_solved': i_solved,
        'i_open': i_released - i_solved,
        'pwa_garciaparra_url': pwa_garciaparra_url, # 2014-specific
        }

def all_teams_update():
    logger.info("updating all teams dashboard...")
    template = loader.get_template('all-teams.html') 
    teams = []
    for team in Team.objects.filter(is_special=False):
        teams.append(TeamDict(team))
    teams.sort(key=lambda team: -(team['r_solved'] * 5)-team['p_solved'])
    q_total = PuzzleSubmission.objects.filter(team__is_special=False, resolved=False).count()
    q_total += MetapuzzleSubmission.objects.filter(team__is_special=False, resolved=False).count()
    q_total += Y2014MitMetapuzzleSubmission.objects.filter(team__is_special=False, resolved=False).count() # 2014-specific
    q_teams = set()
    for x in PuzzleSubmission.objects.filter(team__is_special=False, resolved=False):
        q_teams.add(x.team.url)
    for x in MetapuzzleSubmission.objects.filter(team__is_special=False, resolved=False):
        q_teams.add(x.team.url)
    for x in Y2014MitMetapuzzleSubmission.objects.filter(team__is_special=False, resolved=False): # 2014-specific
        q_teams.add(x.team.url)
    s_total = MAX_POINTS # 2014-specific
    p_total = Puzzle.objects.count()
    r_total = Round.objects.count()
    r_total = r_total - 1 + 3 # 2014-specific
    i_total = Interaction.objects.count()
    i_pending = InteractionAccess.objects.filter(accomplished=False).count()
    i_teams = InteractionAccess.objects.filter(accomplished=False).values('team__url').distinct().count()
    
    context = Context({
        'updated': datetime.now(),
        'teams': teams,
        'q_total': q_total,
        'q_teams': len(q_teams),
        's_total': s_total, # 2014-specific
        'r_total': r_total,
        'p_total': p_total,
        'i_pending': i_pending,
        'i_teams': i_teams,
        'i_total': i_total,
    })
    cache.set('all_teams', template.render(context), 60*60)
    logger.info("...done")

def all_teams_view(request):
    return HttpResponse(cache.get('all_teams'))

def all_puzzles_update():
    logger.info("updating all puzzles dashboard...")
    template = loader.get_template('all-puzzles.html') 
    t_total = Team.objects.filter(is_special=False).count()
    p_total = Puzzle.objects.count()

    def percent(n, d):
        if d == 0 or d < 3:
            return '-'
        return int(n*100/d)

    p_released = 0
    p_solved = 0

    metas = []
    for mm in ['spades', 'clubs', 'diamonds']: # 2014-specific
        meta = Metapuzzle.objects.get(url=mm)
        released = t_total
        solved = MetapuzzleSolve.objects.filter(team__is_special=False, metapuzzle=meta).count()
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
        pf = PuzzleAccess.objects.filter(team__is_special=False, puzzle=mitdata.puzzle)
        released = pf.count()
        solved = PuzzleAccess.objects.filter(team__is_special=False, puzzle=mitdata.puzzle, solved=False).count()
        first_release = None
        if released > 0:
            first_release = pf.order_by('id')[0].timestamp
            p_released += 1
        if solved > 0:
            p_solved += 1
        surveys = PuzzleSurvey.objects.filter(team__is_special=False, puzzle=mitdata.puzzle).values('team__url').distinct().count()
        p = {
            'puzzle': mitdata.puzzle,
            'info': mitdata.card.name,
            'first': first_release,
            'surveys': surveys,
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
            pf = PuzzleAccess.objects.filter(team__is_special=False, puzzle=puzzle)
            released = pf.count()
            solved = PuzzleAccess.objects.filter(team__is_special=False, puzzle=puzzle, solved=True).count()
            surveys = PuzzleSurvey.objects.filter(team__is_special=False, puzzle=mitdata.puzzle).values('team__url').distinct().count()
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
            first_release = None
            if released > 0:
                p_released += 1
                first_release = pf.order_by('id')[0].timestamp
            if solved > 0:
                p_solved += 1
            p = {
                'puzzle': puzzle,
                'info': info,
                'first': first_release,
                'surveys': surveys,
                'released': released,
                'releasedp': percent(released, t_total),
                'solved': solved,
                'solvedp': percent(solved, released),
            }
            puzzles.append(p)
        rf = RoundAccess.objects.filter(team__is_special=False, round=round)
        released = rf.count()
        solved = MetapuzzleSolve.objects.filter(team__is_special=False, metapuzzle=meta).count()
        first_release = None
        if released > 0:
            first_release = rf.order_by('id')[0].timestamp
        m = {
            'meta': meta,
            'puzzles': puzzles,
            'first': first_release,
            'released': released,
            'releasedp': percent(released, t_total),
            'solved': solved,
            'solvedp': percent(solved, released),
        }
        metas.append(m)
    interactions = []
    for interaction in Interaction.objects.all().order_by('id'):
        released = InteractionAccess.objects.filter(team__is_special=False, interaction=interaction).count()
        solved = InteractionAccess.objects.filter(team__is_special=False, interaction=interaction, accomplished=True).count()
        i = {
            'interaction': interaction,
            'released': released,
            'releasedp': percent(released, t_total),
            'solved': solved,
            'solvedp': percent(solved, released),
        }
        interactions.append(i)
        
    i_total = Interaction.objects.count()
    context = Context({
        'updated': datetime.now(),
        'metas': metas,
        'interactions': interactions,
        't_total': t_total,
        'i_total': i_total,
        'p_total': p_total,
        'p_total4': p_total * 4,
        'p_released': p_released,
        'p_released4': p_released * 4,
        'p_releasedp': percent(p_released, p_total),
        'p_solved': p_solved,
        'p_solved4': p_solved * 4,
        'p_solvedp': percent(p_solved, p_total),
    })
    cache.set('all_puzzles', template.render(context), 60*60)
    logger.info("...done")

def all_puzzles_view(request):
    return HttpResponse(cache.get('all_puzzles'))

def one_team_view(request, team_url):
    team = Team.objects.get(url=team_url)
    rounds = []
    for round in Round.objects.all():
        try:
            access = RoundAccess.objects.get(team=team, round=round)
        except:
            access = None
        rounds.append({
            'round': round,
            'access': access,
        })
    metapuzzles = []
    for metapuzzle in Metapuzzle.objects.all():
        solved = MetapuzzleSolve.objects.filter(team=team, metapuzzle=metapuzzle).exists()
        metapuzzles.append({
            'metapuzzle': metapuzzle,
            'solved': solved,
        })
    interactions = []
    for interaction in Interaction.objects.all():
        try:
            access = InteractionAccess.objects.get(team=team, interaction=interaction)
        except:
            access = None
        interactions.append({
            'interaction': interaction,
            'access': access,
        })
    puzzles = []
    for puzzle in Puzzle.objects.all().order_by('round__order', 'order'):
        try:
            access = PuzzleAccess.objects.get(team=team, puzzle=puzzle)
        except:
            access = None
        info = ''
        if puzzle.round.url == 'mit':
            rounddata = Y2014MitPuzzleData.objects.get(puzzle=puzzle)
            info = rounddata.card.name
        if puzzle.round.url == 'tea_party':
            rounddata = Y2014PartyAnswerData.objects.get(answer=puzzle.answer)
            if rounddata.type1 == 'chair':
                info = rounddata.type1+' ('+rounddata.type2+')'
            else:
                info = rounddata.type1+' ('+rounddata.type2+', '+str(rounddata.level)+')'
        if puzzle.round.url == 'caucus_race':
            rounddata = Y2014CaucusAnswerData.objects.filter(yes_answer=puzzle.answer)
            if rounddata.exists():
                info = '%d YES' % rounddata[0].bird
            else:
                rounddata = Y2014CaucusAnswerData.objects.filter(no_answer=puzzle.answer)
                if rounddata.exists():
                    info = '%d NO' % rounddata[0].bird
        if puzzle.round.url == 'knights':
            rounddata = Y2014KnightsAnswerData.objects.get(answer=puzzle.answer)
            info = '%s %s' % (rounddata.color, rounddata.piece)
        puzzles.append({
            'puzzle': puzzle,
            'info': info,
            'access': access,
        })
    context = Context({
        'team': team,
        'phones': TeamPhone.objects.filter(team=team),
        'teamdata': Y2014TeamData.objects.get(team=team), # 2014-specific
        'rounds': rounds,
        'metapuzzles': metapuzzles,
        'interactions': interactions,
        'puzzles': puzzles,
        'surveys': PuzzleSurvey.objects.filter(team=team).order_by('id'),
    })
    template = loader.get_template('one-team.html') 
    return HttpResponse(template.render(context))
