from django.http import HttpResponse, HttpResponseBadRequest
from django.template import RequestContext, loader
from django.shortcuts import redirect

from .models import *
from .actions import *
from .constants import *
from .log import *

def gatekeeper_view(request):
    template = loader.get_template('gatekeeper/start.html') 
    last_points = None
    recent_points = SystemLog.objects.filter(event_type='admin-points').order_by('-id')
    if recent_points.exists():
        last_points = recent_points[0]
    context = RequestContext(request, {
        'interactions': Interaction.objects.all(),
        'events': Puzzle.objects.filter(round__url='events').order_by('order'),
        'last_points': last_points
    })
    return HttpResponse(template.render(context))

def gatekeeper_interaction_view(request):
    if request.method != 'POST' or 'interaction' not in request.POST:
        return HttpResponseBadRequest()
    interaction_url = request.POST['interaction']
    interaction = Interaction.objects.get(url=interaction_url)
    template = loader.get_template('gatekeeper/interaction.html') 
    if 'go' in request.POST:
        ias = []
        for key in request.POST:
            if key[:2] == 't_':
                ias.append(InteractionAccess.objects.get(interaction=interaction, team__url=key[2:]))
        system_log('admin-interaction', 'Registering %d teams as having completed "%s"' % (len(ias), interaction.name))
        for ia in ias:
            interaction_accomplished(ia.team, ia.interaction)
        context = RequestContext(request, {
            'interaction': interaction,
            'done': True,
            'ias': ias,
        })
    else:
        teams_ready = []
        teams_accomplished = []
        teams_not_ready = list(Team.objects.all())
        for ia in InteractionAccess.objects.filter(interaction=interaction):
            teams_not_ready.remove(ia.team)
            if ia.accomplished:
                teams_accomplished.append(ia.team)
            else:
                teams_ready.append(ia.team)
        context = RequestContext(request, {
            'interaction': interaction,
            'teams_not_ready': teams_not_ready,
            'teams_ready': teams_ready,
            'teams_accomplished': teams_accomplished,
        })
    return HttpResponse(template.render(context))

def gatekeeper_event_view(request):
    if request.method != 'POST' or 'event' not in request.POST:
        return HttpResponseBadRequest()
    event_url = request.POST['event']
    event = Puzzle.objects.get(url=event_url)
    template = loader.get_template('gatekeeper/event.html') 
    if 'go' in request.POST:
        system_log('admin-event', 'Releasing event "%s" (because it has occurred)' % (event.name))
        for team in Team.objects.all():
            release_puzzle(team, event, 'This event has occurred')
        context = RequestContext(request, {
            'event': event,
            'done': True,
        })
    else:
        context = RequestContext(request, {
            'event': event,
        })
    return HttpResponse(template.render(context))

def gatekeeper_points_view(request):
    if request.method != 'POST' or 'points' not in request.POST:
        return HttpResponseBadRequest()
    points = int(request.POST['points'])
    template = loader.get_template('gatekeeper/points.html') 
    if 'go' in request.POST:
        reason = request.POST['reason']
        system_log('admin-points', 'granting %d points to all teams (%s)' % (points, reason))
        for t in Team.objects.all():
            grant_points(t, points, reason)
        context = RequestContext(request, {
            'points': points,
            'done': True
        })
    else:
        context = RequestContext(request, {
            'points': points,
            'log': SystemLog.objects.filter(event_type='admin-points').order_by('-id')
        })
    return HttpResponse(template.render(context))
