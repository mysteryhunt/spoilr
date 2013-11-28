from django.http import HttpResponse
from django.template import RequestContext, loader

from .models import *

def TeamDict(team):
    return {
        'team': team
        }

def TeamsArray():
    teams = []
    for team in Team.objects.all():
        teams.append(TeamDict(team))
    return teams

def all_teams(request):
    template = loader.get_template('all-teams.html')
    context = RequestContext(request, {
            'teams': TeamsArray()
            })
    return HttpResponse(template.render(context))
