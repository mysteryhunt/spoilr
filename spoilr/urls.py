from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from .dashboard import all_teams
from .submit import *

urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^submit/puzzle/(\w+)/$', submit_puzzle),
    url(r'^submit/meta/(\w+)/$', submit_metapuzzle),
    url(r'^submit/bait/$', submit_mit_metapuzzle),

    url(r'^hq/all-teams/$', all_teams),
    url(r'^hq/queue/$', queue),
)
