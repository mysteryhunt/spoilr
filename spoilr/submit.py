from django.http import HttpResponse
from django.template import RequestContext, loader
import re

from .models import *
from .actions import *

def cleanup_answer(answer):
    return re.sub(r'[^ A-Z0-9]', '', answer.upper()) 

def compare_answers(a, b):
    return re.sub(r'[^A-Z0-9]', '', a.upper()) == re.sub(r'[^A-Z0-9]', '', b.upper())

def submit_puzzle(request, puzzle_url):
    # TODO SETUP: uncomment, make sure user auth works here
    username = request.META['REMOTE_USER']
    # username = 'bigjimmy'
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
        answer = cleanup_answer(request.POST["answer"])
        phone = request.POST["phone"]
        PuzzleSubmission.objects.create(team=team, puzzle=puzzle, phone=phone, answer=answer).save()
        # hack for testing:
        if answer == "BENOISY" or compare_answers(answer, puzzle.answer):
            puzzle_answer_correct(team, puzzle)
            for sub in PuzzleSubmission.objects.filter(team=team, puzzle=puzzle):
                sub.resolved = True
                sub.save()
    answers = PuzzleSubmission.objects.filter(team=team, puzzle=puzzle)
    solved = PuzzleAccess.objects.get(team=team, puzzle=puzzle).solved
    context = RequestContext(request, {
            'team': team,
            'puzzle': puzzle,
            'solved': solved,
            'answers': answers,
            })
    return HttpResponse(template.render(context))

def submit_metapuzzle(request, metapuzzle_url):
    # TODO SETUP: uncomment, make sure user auth works here
    username = request.META['REMOTE_USER']
    # username = 'bigjimmy'
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
        answer = cleanup_answer(request.POST["answer"])
        phone = request.POST["phone"]
        MetapuzzleSubmission.objects.create(team=team, metapuzzle=metapuzzle, phone=phone, answer=answer).save()
        # hack for testing:
        if answer == "BENOISY" or compare_answers(answer, metapuzzle.answer):
            metapuzzle_answer_correct(team, metapuzzle)
            for sub in MetapuzzleSubmission.objects.filter(team=team, metapuzzle=metapuzzle):
                sub.resolved = True
                sub.save()
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
        answer = cleanup_answer(request.POST["answer"])
        phone = request.POST["phone"]
        Y2014MitMetapuzzleSubmission.objects.create(team=team, phone=phone, answer=answer).save()
        # hack for testing:
        if answer == "DORMOUSE" or compare_answers(answer, Metapuzzle.objects.get(url='dormouse').answer):
            metapuzzle_answer_correct(team, Metapuzzle.objects.get(url='dormouse'))
            for sub in Y2014MitMetapuzzleSubmission.objects.filter(team=team):
                sub.resolved = True
                sub.save()
        if answer == "CATERPILLAR" or compare_answers(answer, Metapuzzle.objects.get(url='caterpillar').answer):
            metapuzzle_answer_correct(team, Metapuzzle.objects.get(url='caterpillar'))
            for sub in Y2014MitMetapuzzleSubmission.objects.filter(team=team):
                sub.resolved = True
                sub.save()
        if answer == "TWEEDLE" or compare_answers(answer, Metapuzzle.objects.get(url='tweedles').answer):
            metapuzzle_answer_correct(team, Metapuzzle.objects.get(url='tweedles'))
            for sub in Y2014MitMetapuzzleSubmission.objects.filter(team=team):
                sub.resolved = True
                sub.save()
    answers = Y2014MitMetapuzzleSubmission.objects.filter(team=team)
    context = RequestContext(request, {
            'team': team,
            'answers': answers,
            })
    return HttpResponse(template.render(context))

def queue(request):
    teams_dict = dict()
    teams = []

    def team_obj(team, timestamp):
        if not team.url in teams_dict:
            team_obj = {"team": team, "timestamp": timestamp, "submissions": []}
            teams_dict[team.url] = team_obj
            teams.append(team_obj)
        else:
            team_obj = teams_dict[team.url]
            if timestamp < team_obj["timestamp"]:
                team_obj["timestamp"] = timestamp
        return team_obj
    
    for sub in PuzzleSubmission.objects.filter(resolved=False):
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "puzzle", "thing": str(sub.puzzle.name), "timestamp": sub.timestamp})
    for sub in MetapuzzleSubmission.objects.filter(resolved=False):
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "metapuzzle", "thing": str(sub.metapuzzle.name), "timestamp": sub.timestamp})
    for sub in Y2014MitMetapuzzleSubmission.objects.filter(resolved=False): # 2014-specific
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "mit-metapuzzle", "thing": "", "timestamp": sub.timestamp})
    for team_obj in teams:
        team_obj["submissions"].sort(key=lambda sub: sub["timestamp"])

    teams.sort(key=lambda team: team["timestamp"])

    template = loader.get_template('queue.html') 
    context = RequestContext(request, {
            'teams': teams,
            })
    return HttpResponse(template.render(context))
