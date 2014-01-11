from django.http import HttpResponse, HttpResponseBadRequest
from django.template import RequestContext, loader
from django.shortcuts import redirect
from django.db import IntegrityError

import re
import datetime

from .models import *
from .actions import *
from .log import *

from . import guess_what_im_thinking

import logging
logger = logging.getLogger(__name__)

def cleanup_answer(answer):
    return re.sub(r'[^ A-Z0-9]', '', answer.upper()) 

def compare_answers(a, b):
    return re.sub(r'[^A-Z0-9]', '', a.upper()) == re.sub(r'[^A-Z0-9]', '', b.upper())

def check_bait(answer): # 2014-specific
    for x in ['spades', 'clubs', 'diamonds']:
        mp = Metapuzzle.objects.get(url=x)
        if compare_answers(answer, mp.answer):
            return mp
    return None

def check_phone(team, phone):
    if TeamPhone.objects.filter(team=team, phone=phone).exists():
        return phone
    fallback = TeamPhone.objects.filter(team=team)[:1].get()
    logger.warning('team %s submitted with phone %s, but they don\'t have that phone in the database - shenanigans? - anyway falling back to %s', team, phone, fallback)
    return fallback

def count_queue(team):
    q = PuzzleSubmission.objects.filter(team=team, resolved=False).count()
    q += MetapuzzleSubmission.objects.filter(team=team, resolved=False).count()
    q += Y2014MitMetapuzzleSubmission.objects.filter(team=team, resolved=False).count() # 2014-specific
    q += Y2014PwaGarciaparraUrlSubmission.objects.filter(team=team, resolved=False).count()
    return q 

def submit_puzzle_answer(team, puzzle, answer, phone):
    if len(answer) == 0:
        return
    for sub in PuzzleSubmission.objects.filter(team=team, puzzle=puzzle):
        if compare_answers(sub.answer, answer):
            return
    if PuzzleAccess.objects.filter(team=team, puzzle=puzzle, solved=True).exists():
        return
    system_log('submit-puzzle', "%s submitted '%s' for %s" % (team.name, answer, str(puzzle)), team=team, object_id=puzzle.url)
    if compare_answers(answer, "BENOISY"): # hack for testing:
        puzzle_answer_correct(team, puzzle)
        return
    try:
        PuzzleSubmission.objects.create(team=team, puzzle=puzzle, phone=phone, answer=answer).save()
    except IntegrityError:
        logger.warning('integrity error adding puzzle submission - this is probably because the team submitted the same answer twice with very little time in between - team:%s puzzle:%s answer:%s', team, puzzle, answer)
        pass        

def submit_puzzle(request, puzzle_url):
    username = request.META['REMOTE_USER']
    try:
        team = Team.objects.get(username=username)
    except:
        logger.exception('cannot find team for user %s', username)
        return HttpResponseBadRequest('cannot find team for user '+username)
    try:
        puzzle = Puzzle.objects.get(url=puzzle_url)
    except:
        logger.exception('cannot find puzzle %s', puzzle_url)
        return HttpResponseBadRequest('cannot find puzzle '+puzzle_url)
    try:
        access = PuzzleAccess.objects.get(team=team, puzzle=puzzle)
    except:
        logger.exception('team %s submitted for puzzle %s, but does not have access to it - shenanigans?', team, puzzle)
        return HttpResponseBadRequest('cannot find puzzle '+puzzle_url)
    q_full1 = count_queue(team) >= QUEUE_LIMIT
    q_full2 = PuzzleSubmission.objects.filter(team=team, puzzle=puzzle, resolved=False).count() >= PUZZLE_QUEUE_LIMIT
    template = loader.get_template('submit/puzzle.html') 
    if request.method == "POST":
        if "survey" in request.POST:
            solved = PuzzleAccess.objects.get(team=team, puzzle=puzzle).solved
            if not solved:
                logger.exception('team %s submitted survey for puzzle %s, but has not solved it - shenanigans?', team, puzzle)
                return HttpResponseBadRequest('cannot submit survey until the puzzle is solved')
            maxlen = PuzzleSurvey._meta.get_field('comment').max_length
            comment = request.POST["comment"][:maxlen]
            fun = request.POST["fun"]
            if fun not in ['1','2','3','4','5']:
                fun = None
            difficulty = request.POST["difficulty"]
            if difficulty not in ['1','2','3','4','5']:
                difficulty = None
            PuzzleSurvey.objects.create(team=team, puzzle=puzzle, fun=fun, difficulty=difficulty, comment=comment).save()
        else:
            if puzzle.url == 'guess_what_im_thinking':
                if 'guess_what_im_thinking' in request.POST:
                    gwit = guess_what_im_thinking.response(request.POST["guess_what_im_thinking"], False)
                    template = loader.get_template('submit/guess_what_im_thinking.html')
                    context = RequestContext(request, {
                        'response': gwit
                    })
                    return HttpResponse(template.render(context))
                else:
                    gwit = guess_what_im_thinking.response(request.POST["answer"])
                    if gwit:
                        template = loader.get_template('submit/guess_what_im_thinking.html')
                        context = RequestContext(request, {
                            'response': gwit
                        })
                        return HttpResponse(template.render(context))
            if not q_full1 and not q_full2:
                maxlen = Puzzle._meta.get_field('answer').max_length
                answer = cleanup_answer(request.POST["answer"])[:maxlen]
                phone = request.POST["phone"]
                phone = check_phone(team, phone)
                submit_puzzle_answer(team, puzzle, answer, phone)
                q_full1 = count_queue(team) >= QUEUE_LIMIT
                q_full2 = PuzzleSubmission.objects.filter(team=team, puzzle=puzzle, resolved=False).count() >= PUZZLE_QUEUE_LIMIT
    solved = PuzzleAccess.objects.get(team=team, puzzle=puzzle).solved
    answers = PuzzleSubmission.objects.filter(team=team, puzzle=puzzle)
    unresolved = answers.filter(resolved=False).exists()
    resolved = answers.filter(resolved=True).exists()
    commentlen = PuzzleSurvey._meta.get_field('comment').max_length
    wq_answer = None
    if puzzle.round.url == 'white_queen':
        pwa = 'puzzle_with_answer_'
        if puzzle.url[:len(pwa)] == pwa:
            wq_answer = cleanup_answer(puzzle.url[len(pwa):])
        elif puzzle.url[:len('another_'+pwa)] == 'another_'+pwa:
            wq_answer = cleanup_answer(puzzle.url[len('another_'+pwa):])
    context = RequestContext(request, {
        'team': team,
        'puzzle': puzzle,
        'wq_answer': wq_answer,
        'solved': solved,
        'answers': answers,
        'unresolved': unresolved,
        'resolved': resolved,
        'commentlen': commentlen,
        'q_full1': q_full1,
        'q_full2': q_full2,
        'q_lim1': QUEUE_LIMIT,
        'q_lim2': PUZZLE_QUEUE_LIMIT,
    })
    return HttpResponse(template.render(context))

def submit_metapuzzle_answer(team, metapuzzle, answer, phone):
    if len(answer) == 0:
        return
    for sub in MetapuzzleSubmission.objects.filter(team=team, metapuzzle=metapuzzle):
        if compare_answers(sub.answer, answer):
            return
    if MetapuzzleSolve.objects.filter(team=team, metapuzzle=metapuzzle).exists():
        return
    system_log('submit-metapuzzle', "%s submitted '%s' for %s" % (team.name, answer, str(metapuzzle)), team=team, object_id=metapuzzle.url)
    if compare_answers(answer, "BENOISY"): # hack for testing:
        metapuzzle_answer_correct(team, metapuzzle)
        return
    try:
        MetapuzzleSubmission.objects.create(team=team, metapuzzle=metapuzzle, phone=phone, answer=answer).save()
    except IntegrityError:
        logger.warning('integrity error adding metapuzzle submission - this is probably because the team submitted the same answer twice with very little time in between - team:%s metapuzzle:%s answer:%s', team, metapuzzle, answer)
        pass        

def submit_metapuzzle(request, metapuzzle_url):
    username = request.META['REMOTE_USER']
    try:
        team = Team.objects.get(username=username)
    except:
        logger.exception('cannot find team for user %s', username)
        return HttpResponseBadRequest('cannot find team for user '+username)
    if metapuzzle_url in ['spades', 'clubs', 'diamonds']: # 2014-specific
        return
    try:
        metapuzzle = Metapuzzle.objects.get(url=metapuzzle_url)
    except:
        logger.exception('cannot find metapuzzle %s', metapuzzle_url)
        return HttpResponseBadRequest('cannot find metapuzzle '+metapuzzle_url)
    q_full1 = count_queue(team) >= QUEUE_LIMIT
    q_full2 = MetapuzzleSubmission.objects.filter(team=team, metapuzzle=metapuzzle, resolved=False).count() >= PUZZLE_QUEUE_LIMIT
    template = loader.get_template('submit/metapuzzle.html') 
    if not q_full1 and not q_full2 and request.method == "POST":
        maxlen = Metapuzzle._meta.get_field('answer').max_length
        answer = cleanup_answer(request.POST["answer"])[:maxlen]
        phone = request.POST["phone"]
        phone = check_phone(team, phone)
        submit_metapuzzle_answer(team, metapuzzle, answer, phone)
        q_full1 = count_queue(team) >= QUEUE_LIMIT
        q_full2 = MetapuzzleSubmission.objects.filter(team=team, metapuzzle=metapuzzle, resolved=False).count() >= PUZZLE_QUEUE_LIMIT
    describe = "Round: %s" % metapuzzle.name
    if metapuzzle.url.startswith("white_queen_a"):
        describe = "Puzzle: ???"
    answers = MetapuzzleSubmission.objects.filter(team=team, metapuzzle=metapuzzle)
    unresolved = answers.filter(resolved=False).exists()
    resolved = answers.filter(resolved=True).exists()
    solved = MetapuzzleSolve.objects.filter(team=team, metapuzzle=metapuzzle).exists()
    context = RequestContext(request, {
        'team': team,
        'describe': describe,
        'metapuzzle': metapuzzle,
        'solved': solved,
        'answers': answers,
        'unresolved': unresolved,
        'resolved': resolved,
        'q_full1': q_full1,
        'q_full2': q_full2,
        'q_lim1': QUEUE_LIMIT,
        'q_lim2': PUZZLE_QUEUE_LIMIT,
    })
    return HttpResponse(template.render(context))

def submit_mit_metapuzzle_answer(team, answer, phone): # 2014-specific
    if len(answer) == 0:
        return
    for sub in Y2014MitMetapuzzleSubmission.objects.filter(team=team):
        if compare_answers(sub.answer, answer):
            return
    system_log('submit-mit-bait', "%s submitted '%s'" % (team.name, answer), team=team)
    for x in ['spades', 'clubs', 'diamonds']: # hack for testing
        if compare_answers(answer, x):
            metapuzzle_answer_correct(team, Metapuzzle.objects.get(url=x))
            return
    try:
        Y2014MitMetapuzzleSubmission.objects.create(team=team, phone=phone, answer=answer).save()
    except IntegrityError:
        logger.warning('integrity error adding bait submission - this is probably because the team submitted the same answer twice with very little time in between - team:%s answer:%s', team, answer)
        pass        

def submit_mit_metapuzzle(request): # 2014-specific
    username = request.META['REMOTE_USER']
    try:
        team = Team.objects.get(username=username)
    except:
        logger.exception('cannot find team for user %s', username)
        return HttpResponseBadRequest('cannot find team for user '+username)
    q_full1 = count_queue(team) >= QUEUE_LIMIT
    q_full2 = Y2014MitMetapuzzleSubmission.objects.filter(team=team, resolved=False).count() >= PUZZLE_QUEUE_LIMIT
    template = loader.get_template('submit/mit-metapuzzle.html') 
    if not q_full1 and not q_full2 and request.method == "POST":
        maxlen = Metapuzzle._meta.get_field('answer').max_length
        answer = cleanup_answer(request.POST["answer"])[:maxlen]
        phone = request.POST["phone"]
        phone = check_phone(team, phone)
        submit_mit_metapuzzle_answer(team, answer, phone)
        q_full1 = count_queue(team) >= QUEUE_LIMIT
        q_full2 = Y2014MitMetapuzzleSubmission.objects.filter(team=team, resolved=False).count() >= PUZZLE_QUEUE_LIMIT
    answers = Y2014MitMetapuzzleSubmission.objects.filter(team=team)
    unresolved = answers.filter(resolved=False).exists()
    resolved = answers.filter(resolved=True).exists()
    solved = []
    for x in ['spades', 'clubs', 'diamonds']:
        for y in MetapuzzleSolve.objects.filter(team=team, metapuzzle__url=x):
            if x == 'spades':
                message = 'The Dormouse took the bait'
            elif x == 'clubs':
                message = 'The Caterpillar took the bait'
            elif x == 'diamonds':
                message = 'Tweedledee and Tweedledum took the bait'
            solved.append({'meta': y.metapuzzle, 'message': message})
    context = RequestContext(request, {
        'team': team,
        'answers': answers,
        'resolved': resolved,
        'unresolved': unresolved,
        'solved': solved,
        'notdone': len(solved) != 3,
        'q_full1': q_full1,
        'q_full2': q_full2,
        'q_lim1': QUEUE_LIMIT,
        'q_lim2': PUZZLE_QUEUE_LIMIT,
    })
    return HttpResponse(template.render(context))

def submit_pwa_garciaparra_url_actual(team, url, phone): # 2014-specific
    if len(url) == 0:
        return
    for sub in Y2014PwaGarciaparraUrlSubmission.objects.filter(team=team):
        if sub.url == url:
            return
    system_log('submit-pwa-garciaparra-url', "%s submitted '%s'" % (team.name, url), team=team)
    if compare_answers(url, 'BENOISY'): # hack for testing
        interaction_accomplished(team, Interaction.objects.get(url='pwa_garciaparra_url'))
        return
    Y2014PwaGarciaparraUrlSubmission.objects.create(team=team, phone=phone, url=url).save()

def submit_pwa_garciaparra_url(request): # 2014-specific
    username = request.META['REMOTE_USER']
    try:
        team = Team.objects.get(username=username)
    except:
        logger.exception('cannot find team for user %s', username)
        return HttpResponseBadRequest('cannot find team for user '+username)
    ia = InteractionAccess.objects.get(team=team, url='pwa_garciaparra_url')
    if ia.accomplished:
        return
    q_full1 = count_queue(team) >= QUEUE_LIMIT
    q_full2 = Y2014PwaGarciaparraUrlSubmission.objects.filter(team=team, resolved=False).count() >= 1
    template = loader.get_template('submit/pwa-garciaparra-url.html') 
    if not q_full1 and not q_full2 and request.method == "POST":
        maxlen = Y2014PwaGarciaparraUrlSubmission._meta.get_field('url').max_length
        url = request.POST["url"][:maxlen]
        phone = request.POST["phone"]
        phone = check_phone(team, phone)
        submit_pwa_garciaparra_url_actual(team, url, phone)
        q_full1 = count_queue(team) >= QUEUE_LIMIT
        q_full2 = Y2014PwaGarciaparraUrlSubmission.objects.filter(team=team, resolved=False).count() >= 1
    urls = Y2014PwaGarciaparraUrlSubmission.objects.filter(team=team, resolved=False)
    context = RequestContext(request, {
        'team': team,
        'urls': urls,
        'q_full1': q_full1,
        'q_full2': q_full2,
        'q_lim1': QUEUE_LIMIT,
        'q_lim2': PUZZLE_QUEUE_LIMIT,
    })
    return HttpResponse(template.render(context))


def submit_contact_actual(team, phone, comment):
    system_log('submit-contact', "%s wants to talk to HQ: '%s'" % (team.name, comment), team=team)
    ContactRequest.objects.create(team=team, phone=phone, comment=comment).save()

def submit_contact(request):
    username = request.META['REMOTE_USER']
    try:
        team = Team.objects.get(username=username)
    except:
        logger.exception('cannot find team for user %s', username)
        return HttpResponseBadRequest('cannot find team for user '+username)
    # these don't count toward the QUEUE_LIMIT
    q_full2 = ContactRequest.objects.filter(team=team, resolved=False).count() >= CONTACT_LIMIT
    template = loader.get_template('submit/contact.html') 
    if not q_full2 and request.method == "POST":
        maxlen = ContactRequest._meta.get_field('comment').max_length
        comment = request.POST["comment"][:maxlen]
        phone = request.POST["phone"]
        phone = check_phone(team, phone)
        submit_contact_actual(team, phone, comment)
        # these don't count toward the QUEUE_LIMIT
        q_full2 = ContactRequest.objects.filter(team=team, resolved=False).count() >= CONTACT_LIMIT
    requests = ContactRequest.objects.filter(team=team, resolved=False)
    context = RequestContext(request, {
        'team': team,
        'requests': requests,
        'q_full2': q_full2,
        'q_lim2': CONTACT_LIMIT,
    })
    return HttpResponse(template.render(context))

def queue(request):
    for h in QueueHandler.objects.all():
        if h.team:
            delta = datetime.now() - h.team_timestamp
            if delta.seconds > 60*10:
                team = h.team
                h.team = None
                h.team_timestamp = None
                h.save()
                logger.warning("handler '%s' (%s) timed out while handling '%s'", h.name, h.email, team.name)
                system_log('queue-timeout', "'%s' (%s) had been handling '%s' for %s seconds, but timed out" % (h.name, h.email, team.name, delta.seconds), team=team)

    handler_email = request.session.get('handler_email')
    handler = None
    if handler_email:
        handler = QueueHandler.objects.get(email=handler_email)
    if request.method == 'POST':
        if "offduty" in request.POST:
            del request.session['handler_email']
        elif "claim" in request.POST:
            team = Team.objects.get(url=request.POST['claim'])
            if count_queue(team) == 0:
                if ContactRequest.objects.filter(team=team, resolved=False).count() == 0:
                    template = loader.get_template('queue/yoinked.html') 
                    context = RequestContext(request)
                    return HttpResponse(template.render(context))
            handler.team = team
            handler.team_timestamp = datetime.now()
            try:
                handler.save()
            except IntegrityError:
                template = loader.get_template('queue/yoinked.html') 
                context = RequestContext(request)
                return HttpResponse(template.render(context))
            system_log('queue-claim', "'%s' (%s) claimed '%s'" % (handler.name, handler.email, team.name), team=team)
        elif handler and handler.team and "handled" in request.POST:
            for key in request.POST:
                if key[:2] == 'p_':
                    p = PuzzleSubmission.objects.get(team=handler.team, resolved=False, id=key[2:])
                    p.resolved = True
                    system_log('queue-resolution', "'%s' (%s) resolved answer '%s' for puzzle '%s' for team '%s'" % (handler.name, handler.email, p.answer, str(p.puzzle), handler.team.name), team=handler.team)
                    if compare_answers(p.answer, p.puzzle.answer):
                        puzzle_answer_correct(handler.team, p.puzzle)
                    else:
                        puzzle_answer_incorrect(handler.team, p.puzzle, p.answer)
                    p.save()
                if key[:2] == 'm_':
                    p = MetapuzzleSubmission.objects.get(team=handler.team, resolved=False, id=key[2:])
                    p.resolved = True
                    system_log('queue-resolution', "'%s' (%s) resolved answer '%s' for metapuzzle '%s' for team '%s'" % (handler.name, handler.email, p.answer, str(p.metapuzzle), handler.team.name), team=handler.team)
                    if compare_answers(p.answer, p.metapuzzle.answer):
                        metapuzzle_answer_correct(handler.team, p.metapuzzle)
                    else:
                        metapuzzle_answer_incorrect(handler.team, p.metapuzzle, p.answer)
                    p.save()
                if key[:2] == 'b_': # 2014-specific
                    p = Y2014MitMetapuzzleSubmission.objects.get(team=handler.team, resolved=False, id=key[2:])
                    p.resolved = True
                    system_log('queue-resolution', "'%s' (%s) resolved bait '%s' for team '%s'" % (handler.name, handler.email, p.answer, handler.team.name), team=handler.team)
                    bait_meta = check_bait(p.answer)
                    if bait_meta:
                        metapuzzle_answer_correct(handler.team, bait_meta)
                    else:
                        mit_bait_incorrect(handler.team, p.answer)
                    p.save()
                if key[:2] == 'c_':
                    p = ContactRequest.objects.get(team=handler.team, resolved=False, id=key[2:])
                    p.resolved = True
                    system_log('queue-resolution', "'%s' (%s) resolved hq-contact '%s' for team '%s'" % (handler.name, handler.email, p.comment, handler.team.name), team=handler.team)
                    p.save()
                if key == 'pwa_garciaparra_url':
                    p = Y2014PwaGarciaparraUrlSubmission.objects.get(team=handler.team, resolved=False)
                    p.resolved = True
                    system_log('queue-resolution', "'%s' (%s) resolved pwa-garciaparra-url '%s' for team '%s'" % (handler.name, handler.email, p.url, handler.team.name), team=handler.team)
                    if 'pwa_garciaparra_url_result' in request.POST and request.POST['pwa_garciaparra_url_result'] == 'good':
                        interaction_accomplished(handler.team, Interaction.objects.get(url='pwa_garciaparra_url'))
                    p.save()
            system_log('queue-claim', "'%s' (%s) released claim on team '%s'" % (handler.name, handler.email, handler.team.name), team=handler.team)
            handler.team = None
            handler.team_timestamp = None
            handler.save()
        elif handler and "handled" in request.POST:
            template = loader.get_template('queue/timedout.html') 
            context = RequestContext(request)
            return HttpResponse(template.render(context))
        elif not handler and "email" in request.POST:
            handler_email = request.POST["email"]
            if QueueHandler.objects.filter(email=handler_email).exists():
                handler = QueueHandler.objects.get(email=handler_email)
            elif "name" in request.POST:
                handler_name = request.POST["name"]
                handler = QueueHandler.objects.create(email=handler_email,name=handler_name)
            else:
                template = loader.get_template('queue/signup.html') 
                context = RequestContext(request, {
                    'email': handler_email,
                })
                return HttpResponse(template.render(context))
            request.session['handler_email'] = handler_email
        return redirect(request.path)

    if handler and handler.team:
        team = handler.team

        phones_other = [x.phone for x in TeamPhone.objects.filter(team=team)]

        phones = set()
        def add_phone(p):
            phones.add(p)
            try:
                phones_other.remove(p)
            except ValueError:
                pass

        puzzle = []
        for p in PuzzleSubmission.objects.filter(team=team, resolved=False):
            puzzle.append({'submission': p, 'correct': compare_answers(p.answer, p.puzzle.answer)})
            add_phone(p.phone)
        metapuzzle = []
        for p in MetapuzzleSubmission.objects.filter(team=team, resolved=False):
            metapuzzle.append({'submission': p, 'correct': compare_answers(p.answer, p.metapuzzle.answer)})
            add_phone(p.phone)
        mitmeta = [] # 2014-specific
        for p in Y2014MitMetapuzzleSubmission.objects.filter(team=team, resolved=False): # 2014-specific
            bait_meta = check_bait(p.answer)
            mitmeta.append({'submission': p, 'correct': not bait_meta is None})
            add_phone(p.phone)
        contact = []
        for p in ContactRequest.objects.filter(team=team, resolved=False):
            contact.append({'submission': p})
            add_phone(p.phone)
        pwagarciaparraurl = [] # 2014-specific
        for p in Y2014PwaGarciaparraUrlSubmission.objects.filter(team=team, resolved=False):
            pwagarciaparraurl.append({'submission': p})
            add_phone(p.phone)

        puzzle.sort(key=lambda p: p['correct'])
        puzzle.sort(key=lambda p: p['submission'].puzzle.url)
        metapuzzle.sort(key=lambda p: p['correct'])
        metapuzzle.sort(key=lambda p: p['submission'].metapuzzle.url)
        mitmeta.sort(key=lambda p: p['correct']) # 2014-specific

        template = loader.get_template('queue/handling.html') 
        context = RequestContext(request, {
            'timer': (60*10 - (datetime.now() - handler.team_timestamp).seconds - 3),
            'handler': handler,
            'phones_other': phones_other,
            'phones_now': phones,
            'puzzle': puzzle,
            'metapuzzle': metapuzzle,
            'mitmeta': mitmeta,
            'contact': contact,
            'pwagarciaparraurl': pwagarciaparraurl,
            'team': team,
        })

        return HttpResponse(template.render(context))

    t_total = Team.objects.count()
    q_total = PuzzleSubmission.objects.filter(resolved=False).count()
    q_total += MetapuzzleSubmission.objects.filter(resolved=False).count()
    q_total += Y2014MitMetapuzzleSubmission.objects.filter(resolved=False).count() # 2014-specific
    q_total += ContactRequest.objects.filter(resolved=False).count()
    q_total += Y2014PwaGarciaparraUrlSubmission.objects.filter(resolved=False).count() # 2014-specific
    q_teams = set()
    for x in PuzzleSubmission.objects.filter(resolved=False):
        q_teams.add(x.team.url)
    for x in MetapuzzleSubmission.objects.filter(resolved=False):
        q_teams.add(x.team.url)
    for x in Y2014MitMetapuzzleSubmission.objects.filter(resolved=False): # 2014-specific
        q_teams.add(x.team.url)
    for x in ContactRequest.objects.filter(resolved=False):
        q_teams.add(x.team.url)
    for x in Y2014PwaGarciaparraUrlSubmission.objects.filter(resolved=False): # 2014-specific
        q_teams.add(x.team.url)

    teams_dict = dict()
    teams = []

    def team_obj(team, timestamp):
        sec = (datetime.now() - timestamp).seconds
        if not team.url in teams_dict:
            team_obj = {"team": team, "youngest": sec, "oldest": sec, "submissions": []}
            teams_dict[team.url] = team_obj
            teams.append(team_obj)
        else:
            team_obj = teams_dict[team.url]
            team_obj["youngest"] = min(sec, team_obj["youngest"])
            team_obj["oldest"] = max(sec, team_obj["oldest"])
        return team_obj
    
    for sub in PuzzleSubmission.objects.filter(resolved=False):
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "puzzle", "thing": str(sub.puzzle), "timestamp": sub.timestamp})
    for sub in MetapuzzleSubmission.objects.filter(resolved=False):
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "metapuzzle", "thing": str(sub.metapuzzle), "timestamp": sub.timestamp})
    for sub in Y2014MitMetapuzzleSubmission.objects.filter(resolved=False): # 2014-specific
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "mit-metapuzzle", "thing": "", "timestamp": sub.timestamp})
    for sub in ContactRequest.objects.filter(resolved=False):
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "contact", "thing": sub.comment, "timestamp": sub.timestamp})
    for sub in Y2014PwaGarciaparraUrlSubmission.objects.filter(resolved=False):
        team_obj(sub.team, sub.timestamp)["submissions"].append({"type": "pwa-garciaparra-url", "thing": sub.url, "timestamp": sub.timestamp})
    for team_obj in teams:
        team_obj["submissions"].sort(key=lambda sub: sub["timestamp"])
        handlers = QueueHandler.objects.filter(team=team_obj["team"])
        if handlers.exists():
            team_obj["handler"] = handlers[0] 

    teams.sort(key=lambda team: -team["oldest"])

    template = loader.get_template('queue/queue.html') 
    context = RequestContext(request, {
        'tq_max': QUEUE_LIMIT,
        't_total': t_total,
        'q_total': q_total,
        'q_teams': len(q_teams),
        'handler': handler,
        'teams': teams,
    })

    if handler:
        handler.activity = datetime.now()
        handler.save()

    return HttpResponse(template.render(context))
