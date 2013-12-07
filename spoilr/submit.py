from django.http import HttpResponse
from django.template import RequestContext, loader

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
    if request.method == "GET":
        template = loader.get_template('submit-puzzle.html') 
        context = RequestContext(request, {
                'team': team,
                'puzzle': puzzle,
                })
        return HttpResponse(template.render(context))
    else:
        answer = request.POST["answer"]
        template = loader.get_template('submit-puzzle-done.html') 
        context = RequestContext(request, {
                'team': team,
                'puzzle': puzzle,
                })
        return HttpResponse(template.render(context))
        
