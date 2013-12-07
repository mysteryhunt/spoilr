from django.http import HttpResponse
from django.template import RequestContext, loader
import re

from .models import *

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
        answer = re.sub(r'[^ A-Z0-9]', '', request.POST["answer"].upper())       
        PuzzleSubmission.objects.create(team=team, puzzle=puzzle, answer=answer).save()
        #template = loader.get_template('submit-puzzle-done.html') 
    answers = PuzzleSubmission.objects.filter(team=team, puzzle=puzzle)
    context = RequestContext(request, {
            'team': team,
            'puzzle': puzzle,
            'answers': answers,
            })
    return HttpResponse(template.render(context))
        
