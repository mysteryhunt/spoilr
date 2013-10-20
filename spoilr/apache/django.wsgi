import os
import sys

path = '/home/djangoapps/spoilr'
if path not in sys.path:
    sys.path.append(path)

path = '/home/djangoapps/spoilr/spoilr'
if path not in sys.path:
    sys.path.append(path)

path = '/home/djangoapps/spoilr-env/lib/python2.7'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'spoilr.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


