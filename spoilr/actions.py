from .log import *
from .models import *
from .constants import *
from .publish import *

import logging

logger = logging.getLogger(__name__)

def release_round(team, round, reason):
    if RoundAccess.objects.filter(team=team, round=round).exists():
        return
    print("release %s/round/%s (%s)" % (team.url, round.url, reason))
    RoundAccess.objects.create(team=team, round=round).save()
    team_log_round_access(team, round, reason)
    def release_initial(apuzzle):
        try:
            release_puzzle(team, apuzzle, 'Round "%s" released' % round.name)
        except Exception as e:
            logger.error('error releasing initial puzzle %s: %s' % (apuzzle.url, e))
    if round.url == "mit": # 2014-specific
        pass
    elif round.url == "tea_party": # 2014-specific
        # tea party starts with all the chair puzzles
        for data in Y2014PartyAnswerData.objects.all():
            if data.type1 == 'chair':
                apuzzle = Puzzle.objects.get(round=round, answer=data.answer)
                release_initial(apuzzle)
    elif round.url == "white_queen": # 2014-specific
        # white queen doesn't release puzzles at first
        # teams must complete 'white_queen_gift' before seeing puzzles
        interaction = Interaction.objects.get(url='white_queen_gift')
        release_interaction(team, interaction, 'Round "%s" released' % round.name)
        # hack for testing:
        interaction_accomplished(team, interaction)
    elif round.url == 'caucus_race': # 2014-specific
        count = 2
        for abird in Y2014CaucusAnswerData.objects.all():
            if count > 0:
                try:
                    release_initial(Puzzle.objects.get(round=round, answer=abird.yes_answer))
                except Exception as e:
                    logger.error('missing caucus puzzle, yes for %s' % str(abird))
                try:
                    release_initial(Puzzle.objects.get(round=round, answer=abird.no_answer))
                except Exception as e:
                    logger.error('missing caucus puzzle, no for %s' % str(abird))
                count = count - 1
    else: # 2014-specific
        # it's a wonderland round, let's release some puzzles in it...
        count = WL_RELEASE_INIT
        for apuzzle in Puzzle.objects.filter(round=round):
            if count > 0:
                release_initial(apuzzle)
                count = count - 1
    publish_team_round(team, round)
    publish_team_top(team)

def release_puzzle(team, puzzle, reason):
    if PuzzleAccess.objects.filter(team=team, puzzle=puzzle).exists():
        return
    print("release %s/puzzle/%s (%s)" % (team.url, puzzle.url, reason))
    PuzzleAccess.objects.create(team=team, puzzle=puzzle).save()
    team_log_puzzle_access(team, puzzle, reason)
    if puzzle.url == 'puzzle_with_answer_garciaparra': # 2014-specific
        release_interaction(team, Interaction.objects.get(url='pwa_garciaparra_url'), '"%s" released' % puzzle.name)
    publish_team_puzzle(team, puzzle)
    publish_team_round(team, puzzle.round)
    publish_team_top(team)

def release_interaction(team, interaction, reason):
    if InteractionAccess.objects.filter(team=team, interaction=interaction).exists():
        return
    print("release %s/interaction/%s (%s)" % (team.url, interaction.url, reason))
    InteractionAccess.objects.create(team=team, interaction=interaction).save()
    team_log_interaction_access(team, interaction, reason)
    publish_team_top(team)

def grant_points(team, amount, reason): # 2014-specific
    print("grant %d points to %s (%s)" % (amount, team.url, reason))
    td = Y2014TeamData.objects.get(team=team)
    pre = td.points
    td.points = td.points + amount
    td.save()
    if pre < DRINK_READY[-1]:
        team_log(team, 'points', 'Gained %d drink-me point(s) (%s)' % (min(DRINK_READY[-1], td.points) - pre, reason))
    if td.points >= DRINK_READY[-1]:
        if pre < TRAIN_READY[-1]:
            team_log(team, 'points', 'Gained %d train ticket point(s) (%s)' % (min(TRAIN_READY[-1], td.points) - max(DRINK_READY[-1], pre), reason))
    # If they've got a full vial now...
    num_wh = 0
    for access in RoundAccess.objects.filter(team=team):
        if access.round.url in ["tea_party", "mock_turtle", "white_queen"]:
            num_wh = num_wh + 1
    if num_wh < 3 and td.points >= DRINK_READY[num_wh]:
        # ...and they've solved a metapuzzle but haven't released the round, release the round (causing the vial to be drunk)
        next_round = None
        if MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='dormouse').exists() and not RoundAccess.objects.filter(team=team, round__url='tea_party').exists():
            next_round = 'tea_party'
        elif MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='caterpillar').exists() and not RoundAccess.objects.filter(team=team, round__url='mock_turtle').exists():
            next_round = 'mock_turtle'
        elif MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='tweedles').exists() and not RoundAccess.objects.filter(team=team, round__url='white_queen').exists():
            next_round = 'white_queen'
        if not next_round is None:
            team_log(team, 'story', 'You filled a drink-me vial, drank it and jumped into a small hole.')
            release_round(team, Round.objects.get(url=next_round), 'Jumped into a rabbit hole')
            team_log(team, 'points', 'Consumed %d drink-me point(s) (Jumped into a rabbit hole)' % DRINK_COST[num_wh])
        elif pre < DRINK_READY[num_wh]:
            team_log_vial_filled_no_hole(team)
    # If they've got a full train ticket now...
    num_wc = 0
    for access in RoundAccess.objects.filter(team=team):
        if access.round.url in ["caucus_race", "knights", "humpty_dumpty"]:
            num_wc = num_wc + 1
    if num_wc < 3 and td.points >= TRAIN_READY[num_wc]:
        # release the next wonderland round
        next_round = None
        if not RoundAccess.objects.filter(team=team, round__url='caucus_race').exists():
            next_round = 'caucus_race'
        elif not RoundAccess.objects.filter(team=team, round__url='knights').exists():
            next_round = 'knights'
        elif not RoundAccess.objects.filter(team=team, round__url='humpty_dumpty').exists():
            next_round = 'humpty_dumpty'
        release_round(team, Round.objects.get(url=next_round), 'You completed a train ticket, and gained access to another location.')
    publish_team_round(team, Round.objects.get(url='mit'))
    publish_team_top(team)            

def puzzle_answer_correct(team, puzzle):
    if not PuzzleAccess.objects.filter(team=team, puzzle=puzzle).exists():
        return
    pa = PuzzleAccess.objects.get(team=team, puzzle=puzzle)
    if pa.solved:
        return
    print("puzzle answer correct %s/puzzle/%s" % (team.url, puzzle.url))
    pa.solved = True
    team_log_puzzle_solved(team, puzzle)
    pa.save()
    publish_team_puzzle(team, puzzle)
    if puzzle.round.url == 'mit': # 2014-specific
        grant_points(team, POINT_INCR_MIT, 'solved an MIT puzzle')
    elif puzzle.round.url != 'events': # 2014-specific
        grant_points(team, POINT_INCR_WL, 'solved a Wonderland puzzle')
    if puzzle.round.url == 'mit': # 2014-specific
        # mit map: release all puzzles connected to the solved one
        card = Y2014MitPuzzleData.objects.get(puzzle=puzzle).card
        for edge in Y2014MitMapEdge.objects.filter(card1=card):
            try:
                release_puzzle(team, Y2014MitPuzzleData.objects.get(card=edge.card2).puzzle, 'connected to "%s"' % puzzle.name)
            except Exception as e:
                logger.error('missing mit puzzle at %s' % (edge.card2))
        for edge in Y2014MitMapEdge.objects.filter(card2=card):
            try:
                release_puzzle(team, Y2014MitPuzzleData.objects.get(card=edge.card1).puzzle, 'connected to "%s"' % puzzle.name)
            except Exception as e:
                logger.error('missing mit puzzle at %s' % (edge.card1))
    elif puzzle.round.url == 'tea_party': # 2014-specific
        # crazy tea party rules:
        chairs = 0
        max_yule = -1
        max_moon = -1
        max_oolong = -1
        level_1 = 0
        level_2 = 0
        def relpuzzle(data, reason):
            try:
                apuzzle = Puzzle.objects.get(round=puzzle.round, answer=data.answer)
                release_puzzle(team, apuzzle, reason)
            except:
                logger.error('missing puzzle in tea party round at ' + str(data))
        for data in Y2014PartyAnswerData.objects.all():
            try:
                apuzzle = Puzzle.objects.get(round=puzzle.round, answer=data.answer)
                if PuzzleAccess.objects.filter(team=team, puzzle=apuzzle, solved=True).exists():
                    if data.type1 == 'chair':
                        chairs += 1
                    else:
                        if data.type2 == 'yule':
                            max_yule = data.level
                        elif data.type2 == 'moon':
                            max_moon = data.level
                        elif data.type2 == 'oolong':
                            max_oolong = data.level
                        if data.level == 1:
                            level_1 += 1
                        elif data.level == 2:
                            level_2 += 1
            except:
                logger.error('missing puzzle in tea party round at ' + str(data))
        if chairs == 4:
            for data in Y2014PartyAnswerData.objects.all():
                if data.type1 == 'cup' and data.level == 2:
                    relpuzzle(data, 'solved all four chair puzzles')
        elif chairs == 2:
            for data in Y2014PartyAnswerData.objects.all():
                if data.type1 == 'cup' and data.level == 1:
                    relpuzzle(data, 'solved two chair puzzles')
        if level_2 == 3:
            for data in Y2014PartyAnswerData.objects.all():
                if data.type1 == 'cup' and data.level == 4:
                    relpuzzle(data, 'solved all three second-tier teacup puzzles')
        elif level_1 == 3:
            for data in Y2014PartyAnswerData.objects.all():
                if data.type1 == 'cup' and data.level == 3:
                    relpuzzle(data, 'solved all three initial teacup puzzles')
        for data in Y2014PartyAnswerData.objects.all():
            if data.type1 == 'cup':
                if data.type2 == 'yule' and data.level == max_yule + 1:
                    relpuzzle(data, 'solved %s' % puzzle.name)
                elif data.type2 == 'moon' and data.level == max_moon + 1:
                    relpuzzle(data, 'solved %s' % puzzle.name)
                elif data.type2 == 'oolong' and data.level == max_oolong + 1:
                    relpuzzle(data, 'solved %s' % puzzle.name)
    elif puzzle.round.url == 'white_queen': # 2014-specific
        # upon solving six white queen puzzles,
        # release three more
        count = PuzzleAccess.objects.filter(team=team, puzzle__round=puzzle.round, solved=True).count()
        if count == 6:
            pwa = 'puzzle_with_answer_'
            for p in [pwa+'eight_days_a_week', pwa+'norwegian_wood', pwa+'love_me_do']:
                try:
                    release_puzzle(team, Puzzle.objects.get(url=p), 'Having found six titles to White Queen puzzles, you remember some more answers')
                except:
                    pass
    elif puzzle.round.url == 'caucus_race': # 2014-specific
        # caucus race releases puzzles in pairs by bird
        for abird in Y2014CaucusAnswerData.objects.all():
            yes_puzzle = None
            no_puzzle = None
            try:
                yes_puzzle = Puzzle.objects.get(round=puzzle.round, answer=abird.yes_answer)
            except Exception as e:
                logger.error('missing caucus puzzle, yes for %s' % str(abird))
            try:
                no_puzzle = Puzzle.objects.get(round=puzzle.round, answer=abird.no_answer)
            except Exception as e:
                logger.error('missing caucus puzzle, no for %s' % str(abird))
            if (yes_puzzle and not PuzzleAccess.objects.filter(team=team, puzzle=yes_puzzle).exists()) or (no_puzzle and not PuzzleAccess.objects.filter(team=team, puzzle=no_puzzle).exists()):
                if yes_puzzle:
                    release_puzzle(team, yes_puzzle, 'solved "%s"' % puzzle.name)
                if no_puzzle:
                    release_puzzle(team, no_puzzle, 'solved "%s"' % puzzle.name)
                break
    else:
        if puzzle.round.url == 'humpty_dumpty': # 2014-specific
            td = Y2014TeamData.objects.get(team=team)
            if td.humpty_pieces < 12:
                td.humpty_pieces = td.humpty_pieces + 1
                td.save()
        # release more puzzles
        count = WL_RELEASE_INCR
        for apuzzle in Puzzle.objects.filter(round=puzzle.round):
            if count > 0 and not PuzzleAccess.objects.filter(team=team, puzzle=apuzzle).exists():
                try:
                    release_puzzle(team, apuzzle, 'solved "%s"' % puzzle.name)
                except Exception as e:
                    logger.error('error releasing additional puzzle %s: %s' % (apuzzle.url, e))
                count = count - 1        
    publish_team_top(team)
    publish_team_round(team, puzzle.round)

def puzzle_answer_incorrect(team, puzzle, answer):
    if not PuzzleAccess.objects.filter(team=team, puzzle=puzzle).exists():
        return
    team_log_puzzle_incorrect(team, puzzle, answer)
    # publish the log
    publish_team_top(team)

def metapuzzle_answer_correct(team, metapuzzle):
    if MetapuzzleSolve.objects.filter(team=team, metapuzzle=metapuzzle).exists():
        return
    print("metapuzzle answer correct %s/metapuzzle/%s" % (team.url, metapuzzle.url))
    team_log_metapuzzle_solved(team, metapuzzle)
    MetapuzzleSolve.objects.create(team=team, metapuzzle=metapuzzle).save()
    if metapuzzle.url in ['dormouse', 'caterpillar', 'tweedles']: # 2014-specific
        interaction = Interaction.objects.get(url=metapuzzle.url)
        release_interaction(team, interaction, "Found the right bait")
        # hack for testing:
        interaction_accomplished(team, interaction)
    if metapuzzle.url in ['tea_party', 'white_queen', 'mock_turtle', 'caucus_race', 'knights', 'white_queen']: # 2014-specific
        if metapuzzle.url == 'tea_party':
            reason = "Solved the Mad Hatter's problem"
        elif metapuzzle.url == 'white_queen':
            reason = "Solved the White Queen's problem"
        elif metapuzzle.url == 'mock_turtle':
            reason = "Solved the Mock Turtle's problem"
        elif metapuzzle.url == 'caucus_race':
            reason = "Found a Weakness of the Beast"
        elif metapuzzle.url == 'knights':
            reason = "Found a Weakness of the Beast"
        elif metapuzzle.url == 'white_queen':
            reason = "Found a Weakness of the Beast"
        grant_points(team, POINT_INCR_WLMETA, reason)
    if metapuzzle.url[:13] == 'white_queen_a': # 2014-specific
        pwa = 'puzzle_with_answer_'
        answers = []
        url = None
        for meta in Metapuzzle.objects.all():
            if meta.url.startswith('white_queen_a'):
                if meta.url == metapuzzle.url:
                    if meta.answer in answers:
                        url = 'another_'+pwa+meta.answer.lower().replace(' ','_')
                    else:
                        url = pwa+meta.answer.lower().replace(' ','_')
                answers.append(meta.answer)
        release_puzzle(team, Puzzle.objects.get(url=url), 'You backsolved this puzzle\'s answer, now find its title')
        publish_team_round(team, Round.objects.get(url='white_queen'))
    if Round.objects.filter(url=metapuzzle.url).exists(): # 2014-specific
        publish_team_round(team, Round.objects.get(url=metapuzzle.url))
    publish_team_top(team)

def metapuzzle_answer_incorrect(team, metapuzzle, answer):
    if MetapuzzleSolve.objects.filter(team=team, metapuzzle=metapuzzle).exists():
        return
    team_log_metapuzzle_incorrect(team, metapuzzle, answer)
    # publish the log
    publish_team_top(team)

def mit_bait_incorrect(team, answer): # 2014-specific
    team_log_mit_bait_incorrect(team, answer)
    # publish the log
    publish_team_top(team)

def interaction_accomplished(team, interaction):
    if not InteractionAccess.objects.filter(team=team, interaction=interaction).exists():
        return
    ia = InteractionAccess.objects.get(team=team, interaction=interaction)
    if ia.accomplished:
        return
    print("interaction accomplished %s/interaction/%s" % (team.url, interaction.url))
    ia.accomplished = True
    team_log_interaction_accomplished(team, interaction)
    ia.save()
    if interaction.url in ['dormouse', 'caterpillar', 'tweedles']: # 2014-specific
        # mit meta: if they have a full vial...
        td = Y2014TeamData.objects.get(team=team)
        num_wh = 0
        for access in RoundAccess.objects.filter(team=team):
            if access.round.url in ["tea_party", "mock_turtle", "white_queen"]:
                num_wh = num_wh + 1
        if num_wh < 3 and td.points >= DRINK_READY[num_wh]:
            # ...release the corresponding round (which causes the vial to be drunk)
            next_round = None
            if interaction.url == 'dormouse':
                next_round = 'tea_party'
            elif interaction.url == 'caterpillar':
                next_round = 'mock_turtle'
            elif interaction.url == 'tweedles':
                next_round = 'white_queen'
            else:
                logger.error('bug in mit round release: %s' % interaction.name)
            if not next_round is None:
                team_log(team, 'story', 'You found a small hole, drank a drink-me vial and jumped in.')
                release_round(team, Round.objects.get(url=next_round), 'Jumped into a rabbit hole')
                team_log(team, 'points', 'Consumed %d drink-me point(s) (Jumped into a rabbit hole)' % DRINK_COST[num_wh])
        else:
            team_log_hole_discovered_no_vial(team)
        publish_team_round(team, Round.objects.get(url='mit'))
    elif interaction.url == 'white_queen_gift': # 2014-specific
        pwa = 'puzzle_with_answer_'
        for p in [pwa+'williams', pwa+'lynn', pwa+'sullivan', 'another_'+pwa+'sullivan', pwa+'rice']:
            try:
                release_puzzle(team, Puzzle.objects.get(url=p), 'You gave the White Queen a gift')
            except:
                pass
        publish_team_round(team, Round.objects.get(url='white_queen'))
    elif interaction.url == 'pwa_garciaparra_url': # 2014-specific 
        release_interaction(team, Interaction.objects.get(url='pwa_garciaparra_food'), 'You beat the White Queen\'s GeoGuessr challenge')
        publish_team_puzzle(team, Puzzle.objects.get(url='puzzle_with_answer_garciaparra'))
    elif interaction.url == 'pwa_garciaparra_food': # 2014-specific 
        publish_team_puzzle(team, Puzzle.objects.get(url='puzzle_with_answer_garciaparra'))
    publish_team_top(team)
