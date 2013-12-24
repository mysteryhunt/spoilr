from django.http import HttpResponse
from django.template import RequestContext, loader
from django.shortcuts import redirect

import re
import datetime

from .models import *
from .actions import *
from .log import *

def cleanup_answer(answer):
    return re.sub(r'[^ A-Z0-9]', '', answer.upper()) 

def compare_answers(a, b):
    return re.sub(r'[^A-Z0-9]', '', a.upper()) == re.sub(r'[^A-Z0-9]', '', b.upper())

def check_phone(team, phone):
    if TeamPhone.objects.filter(team=team, phone=phone).exists():
        return phone
    return TeamPhone.objects.filter(team=team)[:1].get()

def submit_puzzle_answer(team, puzzle, answer, phone):
    if len(answer) == 0:
        return
    for sub in PuzzleSubmission.objects.filter(team=team, puzzle=puzzle):
        if compare_answers(sub.answer, answer):
            return
    if PuzzleAccess.objects.filter(team=team, puzzle=puzzle, solved=True).exists():
        return
    system_log('submit-puzzle', "%s submitted '%s' for %s" % (team.name, answer, str(puzzle)), team=team, object_id=puzzle.url)
    PuzzleSubmission.objects.create(team=team, puzzle=puzzle, phone=phone, answer=answer).save()
    # hack for testing:
    if answer == "BENOISY" or compare_answers(answer, puzzle.answer):
        puzzle_answer_correct(team, puzzle)
        for sub in PuzzleSubmission.objects.filter(team=team, puzzle=puzzle):
            sub.resolved = True
            sub.save()

def submit_puzzle(request, puzzle_url):
    username = request.META['REMOTE_USER']
    try:
        team = Team.objects.get(username=username)
    except:
        return HttpResponseBadRequest('cannot find team for user '+username)
    try:
        puzzle = Puzzle.objects.get(url=puzzle_url)
    except:
        return HttpResponseBadRequest('cannot find puzzle for url '+puzzle_url)
    template = loader.get_template('submit-puzzle.html') 
    if request.method == "POST":
        maxlen = Puzzle._meta.get_field('answer').max_length
        answer = cleanup_answer(request.POST["answer"])[:maxlen]
        phone = request.POST["phone"]
        phone = check_phone(team, phone)
        submit_puzzle_answer(team, puzzle, answer, phone)
    answers = PuzzleSubmission.objects.filter(team=team, puzzle=puzzle)
    solved = PuzzleAccess.objects.get(team=team, puzzle=puzzle).solved
    context = RequestContext(request, {
            'team': team,
            'puzzle': puzzle,
            'solved': solved,
            'answers': answers,
            })
    return HttpResponse(template.render(context))

def submit_metapuzzle_answer(team, metapuzzle, answer, phone):
    if len(answer) == 0:
        return
    for sub in MetapuzzleSubmission.objects.filter(team=team, metapuzzle=metapuzzle):
        if compare_answers(sub.answer, answer):
            return
    if MetapuzzleSolve.objects.filter(team=team, metapuzzle=metapuzzle).exists():
        return
    system_log('submit-metapuzzle', "%s submitted '%s' for %s" % (team.name, answer, str(metapuzzle)), team=team, object_id=metapuzzle.url)
    MetapuzzleSubmission.objects.create(team=team, metapuzzle=metapuzzle, phone=phone, answer=answer).save()
    # hack for testing:
    if answer == "BENOISY" or compare_answers(answer, metapuzzle.answer):
        metapuzzle_answer_correct(team, metapuzzle)
        for sub in MetapuzzleSubmission.objects.filter(team=team, metapuzzle=metapuzzle):
            sub.resolved = True
            sub.save()

def submit_metapuzzle(request, metapuzzle_url):
    username = request.META['REMOTE_USER']
    try:
        team = Team.objects.get(username=username)
    except:
        return HttpResponseBadRequest('cannot find team for user '+username)
    if metapuzzle_url in ['dormouse', 'caterpillar', 'tweedles']: # 2014-specific
        return
    try:
        metapuzzle = Metapuzzle.objects.get(url=metapuzzle_url)
    except:
        return HttpResponseBadRequest('cannot find metapuzzle for url '+metapuzzle_url)
    template = loader.get_template('submit-metapuzzle.html') 
    if request.method == "POST":
        maxlen = Metapuzzle._meta.get_field('answer').max_length
        answer = cleanup_answer(request.POST["answer"])[:maxlen]
        phone = request.POST["phone"]
        phone = check_phone(team, phone)
        submit_metapuzzle_answer(team, metapuzzle, answer, phone)
    describe = "Round: %s" % metapuzzle.name
    if metapuzzle.url.startswith("white_queen_a"):
        describe = "Puzzle: ???"
    answers = MetapuzzleSubmission.objects.filter(team=team, metapuzzle=metapuzzle)
    solved = MetapuzzleSolve.objects.filter(team=team, metapuzzle=metapuzzle).exists()
    context = RequestContext(request, {
            'team': team,
            'describe': describe,
            'metapuzzle': metapuzzle,
            'solved': solved,
            'answers': answers,
            })
    return HttpResponse(template.render(context))

def submit_mit_metapuzzle_answer(team, answer, phone): # 2014-specific
    if len(answer) == 0:
        return
    for sub in Y2014MitMetapuzzleSubmission.objects.filter(team=team):
        if compare_answers(sub.answer, answer):
            return
    system_log('submit-mit-bait', "%s submitted '%s'" % (team.name, answer), team=team)
    Y2014MitMetapuzzleSubmission.objects.create(team=team, phone=phone, answer=answer).save()
    # begin hack for testing:
    metapuzzle = Metapuzzle.objects.get(url='dormouse')
    if answer == "DORMOUSE" or compare_answers(answer, metapuzzle.answer):
        metapuzzle_answer_correct(team, metapuzzle)
        for sub in Y2014MitMetapuzzleSubmission.objects.filter(team=team):
            sub.resolved = True
            sub.save()
    metapuzzle = Metapuzzle.objects.get(url='caterpillar')
    if answer == "CATERPILLAR" or compare_answers(answer, metapuzzle.answer):
        metapuzzle_answer_correct(team, metapuzzle)
        for sub in Y2014MitMetapuzzleSubmission.objects.filter(team=team):
            sub.resolved = True
            sub.save()
    metapuzzle = Metapuzzle.objects.get(url='tweedles')
    if answer == "TWEEDLE" or compare_answers(answer, metapuzzle.answer):
        metapuzzle_answer_correct(team, metapuzzle)
        for sub in Y2014MitMetapuzzleSubmission.objects.filter(team=team):
            sub.resolved = True
            sub.save()
    # end hack

def submit_mit_metapuzzle(request): # 2014-specific
    # TODO SETUP: uncomment, make sure user auth works here
    username = request.META['REMOTE_USER']
    # username = 'bigjimmy'
    try:
        team = Team.objects.get(username=username)
    except:
        return HttpResponseBadRequest('cannot find team for user '+username)
    template = loader.get_template('submit-mit-metapuzzle.html') 
    if request.method == "POST":
        maxlen = Metapuzzle._meta.get_field('answer').max_length
        answer = cleanup_answer(request.POST["answer"])[:maxlen]
        phone = request.POST["phone"]
        phone = check_phone(team, phone)
        submit_mit_metapuzzle_answer(team, answer, phone)
    answers = Y2014MitMetapuzzleSubmission.objects.filter(team=team)
    solved = []
    for x in MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='dormouse'):
        solved.append(x.metapuzzle)
    for x in MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='caterpillar'):
        solved.append(x.metapuzzle)
    for x in MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='tweedles'):
        solved.append(x.metapuzzle)
    context = RequestContext(request, {
            'team': team,
            'answers': answers,
            'solved': solved,
            'notdone': len(solved) != 3,
            })
    return HttpResponse(template.render(context))

def queue(request):
    for h in QueueHandler.objects.all():
        if h.team:
            delta = datetime.now() - h.team_timestamp
            if delta.seconds > 60*10:
                team = h.team
                h.team = None
                h.team_timestamp = None
                h.save()
                system_log('queue-timeout', "'%s' (%s) had been handling '%s' for %s seconds, but timed out" % (h.name, h.email, team.name, delta.seconds), team=team)

    handler_email = request.session.get('handler_email')
    handler = None
    if handler_email:
        handler = QueueHandler.objects.get(email=handler_email)
    if request.method == 'POST':
        if "offduty" in request.POST:
            del request.session['handler_email']
        elif "claim" in request.POST:
            team = Team.objects.get(url=request.POST['claim'])
            handler.team = team
            handler.team_timestamp = datetime.now()
            handler.save()
            system_log('queue-claim', "'%s' (%s) claims '%s'" % (h.name, h.email, team.name), team=h.team)
        else:
            handler_email = request.POST["email"]
            if QueueHandler.objects.filter(email=handler_email).exists():
                handler = QueueHandler.objects.get(email=handler_email)
            elif "name" in request.POST:
                handler_name = request.POST["name"]
                handler = QueueHandler.objects.create(email=handler_email,name=handler_name)
            else:
                template = loader.get_template('queue-signup.html') 
                context = RequestContext(request, {
                    'email': handler_email,
                })
                return HttpResponse(template.render(context))
            request.session['handler_email'] = handler_email
        return redirect(request.path)

    if handler and handler.team:
        team = handler.team

        phones_other = [x.phone for x in TeamPhone.objects.filter(team=team)]

        phones = set()
        def add_phone(p):
            phones.add(p)
            try:
                phones_other.remove(p)
            except ValueError:
                pass

        puzzle = []
        for p in PuzzleSubmission.objects.filter(team=team, resolved=False):
            puzzle.append({'submission': p, 'correct': compare_answers(p.answer, p.puzzle.answer)})
            add_phone(p.phone)
        metapuzzle = []
        for p in MetapuzzleSubmission.objects.filter(team=team, resolved=False):
            metapuzzle.append({'submission': p, 'correct': compare_answers(p.answer, p.metapuzzle.answer)})
            add_phone(p.phone)
        mitmeta = [] # 2014-specific
        for p in Y2014MitMetapuzzleSubmission.objects.filter(team=team, resolved=False): # 2014-specific
            correct = False
            mp = Metapuzzle.objects.get(url='dormouse')
            if compare_answers(p.answer, mp.answer):
                correct = True
            mp = Metapuzzle.objects.get(url='caterpillar')
            if compare_answers(p.answer, mp.answer):
                correct = True
            mp = Metapuzzle.objects.get(url='tweedles')
            if compare_answers(p.answer, mp.answer):
                correct = True
            mitmeta.append({'submission': p, 'correct': correct})
            add_phone(p.phone)

        template = loader.get_template('queue-handling.html') 
        context = RequestContext(request, {
            'timer': (60*10 - (datetime.now() - handler.team_timestamp).seconds - 3),
            'handler': handler,
            'phones_other': phones_other,
            'phones_now': phones,
            'puzzle': puzzle,
            'metapuzzle': metapuzzle,
            'mitmeta': mitmeta,
            'team': team,
        })

        return HttpResponse(template.render(context))

    t_total = Team.objects.count()
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

    teams_dict = dict()
    teams = []

    def team_obj(team, timestamp):
        sec = (datetime.now() - timestamp).seconds
        if not team.url in teams_dict:
            team_obj = {"team": team, "youngest": sec, "oldest": sec, "submissions": []}
            teams_dict[team.url] = team_obj
            teams.append(team_obj)
        else:
            team_obj = teams_dict[team.url]
            team_obj["youngest"] = min(sec, team_obj["youngest"])
            team_obj["oldest"] = max(sec, team_obj["oldest"])
        return team_obj
    
    for sub in PuzzleSubmission.objects.filter(resolved=False):
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "puzzle", "thing": str(sub.puzzle), "timestamp": sub.timestamp})
    for sub in MetapuzzleSubmission.objects.filter(resolved=False):
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "metapuzzle", "thing": str(sub.metapuzzle), "timestamp": sub.timestamp})
    for sub in Y2014MitMetapuzzleSubmission.objects.filter(resolved=False): # 2014-specific
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "mit-metapuzzle", "thing": "", "timestamp": sub.timestamp})
    for team_obj in teams:
        team_obj["submissions"].sort(key=lambda sub: sub["timestamp"])

    teams.sort(key=lambda team: -team["oldest"])

    template = loader.get_template('queue.html') 
    context = RequestContext(request, {
        'tq_max': QUEUE_LIMIT,
        't_total': t_total,
        'q_total': q_total,
        'q_teams': len(q_teams),
        'handler': handler,
        'teams': teams,
    })

    if handler:
        handler.activity = datetime.now()
        handler.save()

    return HttpResponse(template.render(context))
