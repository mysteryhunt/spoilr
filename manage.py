#!/usr/bin/env python
import os
import sys
import django

if __name__ == "__main__":
    if os.getuid() == 0:
        print "DO NOT ATTEMPT TO MANAGE SPOILR AS ROOT! Use manage wrapper."
        exit (1)

    if (django.VERSION[0] != 1 or django.VERSION[1] < 5):
	sys.stderr.write("Spoilr requires django version 1.5 or greater. django.VERSION() = %d.%d\n" % (django.VERSION[0], django.VERSION[1]))
        exit (1)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spoilr.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
