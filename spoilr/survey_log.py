from django.http import HttpResponse
from django.template import Context, loader
from django.core.cache import cache

from .models import *

def survey_log_update():
    print("updating survey log view...")
    entries = PuzzleSurvey.objects.all().order_by('-id')
    template = loader.get_template('survey-log.html') 
    context = Context({
        'updated': datetime.now(),
        'entries': entries,
    })
    cache.set('survey_log', template.render(context), 60*60)
    print("...done")

def survey_log_view(request):
    return HttpResponse(cache.get('survey_log'))
