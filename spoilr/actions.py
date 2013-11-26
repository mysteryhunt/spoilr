from .log import *
from .models import *
from .constants import *
from .publish import *

import logging

logger = logging.getLogger(__name__)

def release_round(team, round, reason):
    if RoundAccess.objects.filter(team=team, round=round).exists():
        return
    RoundAccess.objects.create(team=team, round=round).save()
    team_log_round_access(team, round, reason)
    publish_team_round(team, round)
    publish_team_top(team)

def release_puzzle(team, puzzle, reason):
    if PuzzleAccess.objects.filter(team=team, puzzle=puzzle).exists():
        return
    PuzzleAccess.objects.create(team=team, puzzle=puzzle).save()
    team_log_puzzle_access(team, puzzle, reason)
    publish_team_puzzle(team, puzzle)
    publish_team_round(team, puzzle.round)
    publish_team_top(team)

def grant_drink_points(team, amount, reason): # 2014-specific
    td = Y2014TeamData.objects.get(team=team)
    pre = td.drink_points
    # If they've got all the drink points they'll ever need...
    if td.drink_points + amount > DRINK_COST * 3:
        # ...turn the extra into train points
        extra = td.drink_points + amount - DRINK_COST * 3
        td.train_points = td.train_points + extra
        td.drink_points = DRINK_COST * 3
    else:
        td.drink_points = td.drink_points + amount
    post = td.drink_points
    td.save()
    # If they've got a full vial now...
    undrunk = td.drink_points
    for access in RoundAccess.objects.filter(team=team):
        if access.round.url in ["tea_party", "mock_turtle", "white_queen"]:
            undrunk = undrunk - DRINK_COST
    if undrunk >= DRINK_COST:
        # ...and they've solved a metapuzzle but haven't released the round, release the round (causing the vial to be drunk)
        next_round = None
        if MetapuzzleSolve.objects.filter(team=team, metapuzzle__name='The Dormouse').exists() and not RoundAccess.objects.filter(team=team, round__url='tea_party').exists():
            next_round = 'tea_party'
        elif MetapuzzleSolve.objects.filter(team=team, metapuzzle__name='The Caterpillar').exists() and not RoundAccess.objects.filter(team=team, round__url='mock_turtle').exists():
            next_round = 'mock_turtle'
        elif MetapuzzleSolve.objects.filter(team=team, metapuzzle__name='Tweedledee and Tweedledum').exists() and not RoundAccess.objects.filter(team=team, round__url='white_queen').exists():
            next_round = 'white_queen'
        if not next_round is None:
            release_round(team, Round.objects.get(url=next_round), 'You filled a drink-me vial, drank it and jumped into a small hole.')
        elif int(pre/DRINK_COST) != int(post/DRINK_COST):
            team_log_vial_filled_no_hole(team)
    publish_team_round(team, Round.objects.get(url='mit'))
            

def puzzle_answer_correct(team, puzzle):
    if not PuzzleAccess.objects.filter(team=team, puzzle=puzzle).exists():
        return
    pa = PuzzleAccess.objects.get(team=team, puzzle=puzzle)
    if pa.solved:
        return
    pa.solved = True
    team_log_puzzle_solved(team, puzzle)
    pa.save()
    publish_team_puzzle(team, puzzle)
    if puzzle.round.url == 'mit': # 2014-specific
        grant_drink_points(team, DRINK_INCR_MIT, 'solved an MIT puzzle')
        # mit map: release all puzzles connected to the solved one
        node = Y2014MitPuzzleData.objects.get(puzzle=puzzle).location
        for edge in Y2014MitMapEdge.objects.filter(node1=node):
            try:
                other_puzzle = Y2014MitPuzzleData.objects.get(location=edge.node2).puzzle
                release_puzzle(team, other_puzzle, 'connected to "%s"' % puzzle.name)
            except Exception as e:
                logger.error('error releasing connecting puzzle at %s: %s' % (edge.node2, e))
        for edge in Y2014MitMapEdge.objects.filter(node2=node):
            try:
                other_puzzle = Y2014MitPuzzleData.objects.get(location=edge.node1).puzzle
                release_puzzle(team, other_puzzle, 'connected to "%s"' % puzzle.name)
            except Exception as e:
                logger.error('error releasing connecting puzzle at %s: %s' % (edge.node1, e))
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
    team_log_metapuzzle_solved(team, metapuzzle)
    MetapuzzleSolve.objects.create(team=team, metapuzzle=metapuzzle).save()
    if metapuzzle.name in ['The Dormouse', 'The Caterpillar', 'Tweedledee and Tweedledum']: # 2014-specific
        # mit meta: if they have a full vial...
        td = Y2014TeamData.objects.get(team=team)
        undrunk = td.drink_points
        for access in RoundAccess.objects.filter(team=team):
            if access.round.url in ["tea_party", "mock_turtle", "white_queen"]:
                undrunk = undrunk - DRINK_COST
        if undrunk >= DRINK_COST:
            # ...release the corresponding round (which causes the vial to be drunk)
            next_round = None
            if metapuzzle.name == 'The Dormouse':
                next_round = 'tea_party'
            elif metapuzzle.name == 'The Caterpillar':
                next_round = 'mock_turtle'
            elif metapuzzle.name == 'Tweedledee and Tweedledum':
                next_round = 'white_queen'
            else:
                logger.error('bug in mit round release: %s' % metapuzzle.name)
            if not next_round is None:
                release_round(team, Round.objects.get(url=next_round), 'You found a small hole, drank a drink-me vial and jumped in.')
        else:
            team_log_hole_discovered_no_vial(team)
        publish_team_round(team, Round.objects.get(url='mit'))
    if metapuzzle.name == 'The White Queen (Gift)': # 2014-specific
        publish_team_round(team, Round.objects.get(url='white_queen'))
    publish_team_top(team)

def metapuzzle_answer_incorrect(team, metapuzzle, answer):
    if MetapuzzleSolve.objects.filter(team=team, metapuzzle=metapuzzle).exists():
        return
    team_log_metapuzzle_incorrect(team, metapuzzle, answer)
    # publish the log
    publish_team_top(team)