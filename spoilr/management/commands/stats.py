from django.core.management.base import BaseCommand
from spoilr.models import *
from spoilr.submit import *

import datetime

class Command(BaseCommand):
    help = """Generates lots of data about the hunt.
"""

    def handle(self, *args, **options):
        begin = datetime.datetime(year=2014, month=1, day=17, hour=12)

        # wrong answers
        print('wrong answers')
        wa = dict()
        for s in PuzzleSubmission.objects.filter(team__is_special=False):
            if not compare_answers(s.answer, s.puzzle.answer):
                k = '%s\t%s\t%s' % (s.puzzle.name, s.puzzle.round.name, s.answer)
                if k not in wa:
                    wa[k] = 0
                wa[k] += 1
        for s in MetapuzzleSubmission.objects.filter(team__is_special=False):
            if not compare_answers(s.answer, s.metapuzzle.answer):
                k = '%s\t\t%s' % (s.metapuzzle.name, s.answer)
                if k not in wa:
                    wa[k] = 0
                wa[k] += 1
        with open('/tmp/wrong_answers.txt','w') as out:
            out.write('%s\t%s\t%s\t%s\n' % ('object', 'round', 'answer', 'count'))
            for k in wa:
                out.write('%s\t%d\n' % (k, wa[k]))
        
        # submit rate
        print('submit rate time series')
        sr = dict()
        def do_sr(s):
            t = s.timestamp.strftime('%a %H')
            k = '%s\t%s' % (t, s.team)
            if k not in sr:
                sr[k] = 0
            sr[k] += 1
        for s in PuzzleSubmission.objects.filter(team__is_special=False):
            do_sr(s)
        for s in MetapuzzleSubmission.objects.filter(team__is_special=False):
            do_sr(s)
        for s in Y2014MitMetapuzzleSubmission.objects.filter(team__is_special=False):
            do_sr(s)
        for s in Y2014PwaGarciaparraUrlSubmission.objects.filter(team__is_special=False):
            do_sr(s)
        with open('/tmp/submit_rate.txt','w') as out:
            out.write('%s\t%s\t%s\n' % ('hour', 'team', 'count'))
            for k in sr:
                out.write('%s\t%d\n' % (k, sr[k]))

        # puzzle surveys
        print('puzzle surveys')
        fp = dict()
        with open('/tmp/puzzle_surveys.txt', 'w') as out:
            out.write('%s\t%s\t%s\t%s\t%s' % ('puzzle', 'round', 'team', 'fun', 'difficulty'))
            for s in PuzzleSurvey.objects.filter(team__is_special=False):
                f = ''
                d = ''
                if s.fun:
                    f = str(s.fun)
                if s.difficulty:
                    d = str(s.difficulty)
                out.write('%s\t%s\t%s\t%s\t%s\n' % (s.puzzle.name, s.puzzle.round, s.team, f, d))

        # solve times
        print('solve times')
        with open('/tmp/solve_times.txt', 'w') as out:
            out.write('%s\t%s\t%s\t%s\t%s\n' % ('puzzle', 'round', 'team', 'duration', 'finish'))
            for s in SystemLog.objects.filter(event_type='puzzle-solved', team__is_special=False):
                p = Puzzle.objects.get(url=s.object_id)
                st = s.timestamp
                a = SystemLog.objects.get(event_type='puzzle-access', team=s.team, object_id = s.object_id)
                at = a.timestamp
                out.write('%s\t%s\t%s\t%f\t%f\n' % (p.name, p.round.name, s.team, (st - at).total_seconds() / 3600.0, (st - begin).total_seconds() / 3600.0))

        # puzzle counts
        print('puzzle count time series')
        with open('/tmp/puzzle_counts.txt', 'w') as out:
            out.write('%s\t%s\t%s\t%s\n' % ('team', 'hour', 'released', 'solved'))
            end = SystemLog.objects.all().order_by('-id')[0].timestamp
            cur = begin
            while cur < end:
                cur += datetime.timedelta(hours=1)
                ts = cur.strftime('%a %H')
                for t in Team.objects.filter(is_special=False):
                    r = SystemLog.objects.filter(event_type='puzzle-access', team=t, timestamp__lt=cur).count()
                    s = SystemLog.objects.filter(event_type='puzzle-solved', team=t, timestamp__lt=cur).count()
                    out.write('%s\t%s\t%d\t%d\n' % (t.name, ts, r, s))

        # contact messages
        print('contat messages')
        with open('/tmp/contact_messages.txt', 'w') as out:
            out.write('%s\t%s\t%s\n' % ('team', 'hour', 'message'))
            for cr in ContactRequest.objects.filter(team__is_special=False):
                t = cr.timestamp.strftime('%a %H')
                out.write('%s\t%s\t%s\n' % (cr.team, t, cr.comment))
