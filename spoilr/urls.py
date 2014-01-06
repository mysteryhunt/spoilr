from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from .dashboard import all_teams_view
from .gatekeeper import *
from .log import system_log_view
from .submit import *

urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^submit/puzzle/(\w+)/$', submit_puzzle),
    url(r'^submit/meta/(\w+)/$', submit_metapuzzle),
    url(r'^submit/bait/$', submit_mit_metapuzzle),
    url(r'^submit/contact/$', submit_contact),
    url(r'^submit/pwa-garciaparra-url/$', submit_pwa_garciaparra_url),

    url(r'^hq/all-teams/$', all_teams_view),
    url(r'^hq/queue/$', queue),
    url(r'^hq/log/$', system_log_view),

    url(r'^hq/gatekeeper/$', gatekeeper_view),
    url(r'^hq/gatekeeper/interaction/$', gatekeeper_interaction_view),
    url(r'^hq/gatekeeper/points/$', gatekeeper_points_view),
)
