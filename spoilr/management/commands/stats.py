from django.core.management.base import BaseCommand
from spoilr.models import *
from spoilr.submit import *

import datetime

class Command(BaseCommand):
    help = """Generates lots of data about the hunt.
"""

    def handle(self, *args, **options):
        begin = datetime.datetime(year=2014, month=1, day=17, hour=12)

        # crossed wires aha
        print('crossed wires aha')
        with open('/tmp/crossed_wires.txt', 'w') as out:
            out.write('%s\t%s\n' % ('team', 'duration'))
            for t in Team.objects.filter(is_special=False):
                s = SystemLog.objects.filter(event_type='puzzle-solved', team=t, object_id='crossed_wires')
                i = SystemLog.objects.filter(event_type='puzzle-incorrect', team=t, object_id='crossed_wires')
                if not i.exists():
                    if not s.exists():
                        continue
                    out.write('%s\t%f\n' % (t.name, 0.0))
                    continue
                r = [x for x in i if 'DELTA' in x.message]
                if len(r) == 0:
                    if not s.exists():
                        continue
                    out.write('%s\t%f\n' % (t.name, 0.0))
                    continue
                if not s.exists():
                    out.write('%s\t\n' % (t.name))
                    continue
                out.write('%s\t%f\n' % (t.name, (s[0].timestamp - r[0].timestamp).total_seconds() / 3600.0))

        # wrong answers
        print('wrong answers')
        wa = dict()
        for s in PuzzleSubmission.objects.filter(team__is_special=False):
            if not compare_answers(s.answer, s.puzzle.answer):
                a = re.sub(r'[^A-Z0-9]', '', s.answer)
                k = '%s\t%s\t%s' % (s.puzzle.name, s.puzzle.round.name, a)
                if k not in wa:
                    wa[k] = 0
                wa[k] += 1
        for s in MetapuzzleSubmission.objects.filter(team__is_special=False):
            if not compare_answers(s.answer, s.metapuzzle.answer):
                a = re.sub(r'[^A-Z0-9]', '', s.answer)
                k = '%s\t\t%s' % (s.metapuzzle.name, a)
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
            th = (s.timestamp - begin).total_seconds() / 3600
            k = '%d\t%s\t%s' % (th, t, s.team)
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
            out.write('%s\t%s\t%s\t%s\n' % ('hour', 'hourdesc', 'team', 'count'))
            for k in sr:
                out.write('%s\t%d\n' % (k, sr[k]))

        # puzzle surveys
        print('puzzle surveys')
        fp = dict()
        with open('/tmp/puzzle_surveys.txt', 'w') as out:
            out.write('%s\t%s\t%s\t%s\t%s\n' % ('puzzle', 'round', 'team', 'fun', 'difficulty'))
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
                a = SystemLog.objects.filter(event_type='puzzle-access', team=s.team, object_id = s.object_id).order_by('-id')[0]
                at = a.timestamp
                out.write('%s\t%s\t%s\t%f\t%f\n' % (p.name, p.round.name, s.team, (st - at).total_seconds() / 3600.0, (st - begin).total_seconds() / 3600.0))

        # meta solve times
        print('meta solve times')
        with open('/tmp/meta_solve_times.txt', 'w') as out:
            out.write('%s\t%s\t%s\t%s\n' % ('meta', 'team', 'duration', 'finish'))
            for s in SystemLog.objects.filter(event_type='metapuzzle-solved', team__is_special=False):
                if s.object_id in ['clubs', 'spades', 'diamonds']:
                    at = begin
                else:
                    if not Round.objects.filter(url=s.object_id).exists():
                        continue
                    at = RoundAccess.objects.get(team=s.team, round__url=s.object_id).timestamp
                st = s.timestamp
                out.write('%s\t%s\t%f\t%f\n' % (s.object_id, s.team, (st - at).total_seconds() / 3600.0, (st - begin).total_seconds() / 3600.0))

        # meta puzzle count
        print('meta puzzle counts')
        with open('/tmp/meta_puzzle_counts.txt', 'w') as out:
            out.write('%s\t%s\t%s\n' % ('meta', 'team', 'count'))
            for s in SystemLog.objects.filter(event_type='metapuzzle-solved', team__is_special=False):
                c = 0
                if s.object_id in ['clubs', 'spades', 'diamonds']:
                    at = begin
                    for p in Y2014MitPuzzleData.objects.filter(puzzle__round__url='mit'):
                        if s.object_id in p.card.name:
                            if SystemLog.objects.filter(event_type='puzzle-solved', team=s.team, object_id=p.puzzle.url, timestamp__lt=s.timestamp):
                                c += 1
                else:
                    if not Round.objects.filter(url=s.object_id).exists():
                        continue
                    for p in Puzzle.objects.filter(round__url=s.object_id):
                        if SystemLog.objects.filter(event_type='puzzle-solved', team=s.team, object_id=p.url, timestamp__lt=s.timestamp):
                            c += 1
                out.write('%s\t%s\t%d\n' % (s.object_id, s.team, c))

        # puzzle counts
        print('puzzle count time series')
        with open('/tmp/puzzle_counts.txt', 'w') as out:
            out.write('%s\t%s\t%s\t%s\t%s\n' % ('team', 'hour', 'hourdesc', 'released', 'solved'))
            end = SystemLog.objects.all().order_by('-id')[0].timestamp
            cur = begin
            while cur < end:
                cur += datetime.timedelta(hours=1)
                ts = cur.strftime('%a %H')
                th = (cur - begin).total_seconds() / 3600
                for t in Team.objects.filter(is_special=False):
                    r = SystemLog.objects.filter(event_type='puzzle-access', team=t, timestamp__lt=cur).count()
                    s = SystemLog.objects.filter(event_type='puzzle-solved', team=t, timestamp__lt=cur).count()
                    out.write('%s\t%d\t%s\t%d\t%d\n' % (t.name, th, ts, r, s))

        # contact messages
        print('contat messages')
        with open('/tmp/contact_messages.txt', 'w') as out:
            out.write('%s\t%s\t%s\t%s\n' % ('team', 'hour', 'hourdesc', 'message'))
            for cr in ContactRequest.objects.filter(team__is_special=False):
                t = cr.timestamp.strftime('%a %H')
                th = (cr.timestamp - begin).total_seconds() / 3600
                out.write('%s\t%d\t%s\t%s\n' % (cr.team, th, t, cr.comment))

        # operator test aha
        print('operator test aha')
        with open('/tmp/operator_test.txt', 'w') as out:
            out.write('%s\t%s\n' % ('team', 'duration'))
            for t in Team.objects.filter(is_special=False):
                s = SystemLog.objects.filter(event_type='puzzle-solved', team=t, object_id='operator_test')
                i = SystemLog.objects.filter(event_type='puzzle-incorrect', team=t, object_id='operator_test')
                if not i.exists():
                    if not s.exists():
                        continue
                    out.write('%s\t%f\n' % (t.name, 0.0))
                    continue
                r = [x for x in i if 'QUAGMIRE' in x.message]
                if len(r) == 0:
                    if not s.exists():
                        continue
                    out.write('%s\t%f\n' % (t.name, 0.0))
                    continue
                if not s.exists():
                    out.write('%s\t\n' % (t.name))
                    continue
                out.write('%s\t%f\n' % (t.name, (s[0].timestamp - r[0].timestamp).total_seconds() / 3600.0))

        # points over time
        print('points time series')
        with open('/tmp/points.txt', 'w') as out:
            out.write('%s\t%s\t%s\t%s\n' % ('team', 'hour', 'hourdesc', 'points'))
            end = SystemLog.objects.all().order_by('-id')[0].timestamp
            cur = begin
            while cur < end:
                cur += datetime.timedelta(hours=1)
                ts = cur.strftime('%a %H')
                th = (cur - begin).total_seconds() / 3600
                for t in Team.objects.filter(is_special=False):
                    p = 0
                    for ps in PuzzleAccess.objects.filter(team=t, solved=True):
                        if SystemLog.objects.filter(event_type='puzzle-solved', team=t, timestamp__lt=cur, object_id=ps.puzzle.url).exists():
                            if ps.puzzle.round.url == 'mit':
                                p += 2
                            else:
                                p += 3
                    out.write('%s\t%d\t%s\t%d\n' % (t.name, th, ts, p))

        # queue wait time
        print('queue wait time')
        l = dict()
        for r in SystemLog.objects.filter(event_type='queue-resolution'):
            l[r.message] = r.timestamp
        h = dict()
        qn = dict()
        qd = dict()
        for s in PuzzleSubmission.objects.all():
            th = '%d' % ((s.timestamp - begin).total_seconds() / 3600)
            ts = s.timestamp.strftime('%a %H')
            h[th] = ts
            if th not in qn:
                print('  '+ts)
                qn[th] = 0
            if th not in qd:
                qd[th] = 0
            #print("looking for '%s' '%s' '%s'" % (s.puzzle, s.answer, s.team))
            for r in l:
                #print("  %s" % r.message)
                if ("'%s'" % s.puzzle) in r and ("'%s'" % s.answer) in r and ("'%s'" % s.team) in r:
                    qn[th] += (l[r] - s.timestamp).total_seconds() / 3600.0
                    qd[th] += 1
                    break
        with open('/tmp/queue_wait_time.txt', 'w') as out:
            out.write('%s\t%s\t%s\n' % ('hour', 'hourdesc', 'time'))
            for ah in qn:
                n = qn[ah]
                d = qd[ah]
                if d == 0:
                    d = 1
                out.write('%s\t%s\t%f\n' % (ah, h[ah], (n/d)))
