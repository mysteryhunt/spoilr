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
    # username = request.META['REMOTE_USER']
    username = 'bigjimmy'
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
        if compare_answers(answer, puzzle.answer):
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

def queue(request):
    submissions = PuzzleSubmission.objects.all()
    teams_dict = dict()
    teams = []
    for sub in submissions:
        if not sub.team.url in teams_dict:
            team_obj = {"team": sub.team, "timestamp": sub.timestamp, "puzzle_submissions": []}
            teams_dict[sub.team.url] = team_obj
            teams.append(team_obj)
        else:
            team_obj = teams_dict[sub.team.url]
        team_obj["puzzle_submissions"].append(sub)
    template = loader.get_template('queue.html') 
    context = RequestContext(request, {
            'teams': teams,
            })
    return HttpResponse(template.render(context))
