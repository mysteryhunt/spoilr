from django.conf import settings

import logging
import csv
import shutil
from .log import *
from .models import *

logger = logging.getLogger(__name__)

def get_team_path(team):
    return os.path.join(settings.TEAMS_DIR, team.url)

def load_metapuzzles():
    print("Loading metapuzzles from metapuzzles.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'metapuzzles.txt'), 'r') as team_file:
        for row in csv.DictReader(team_file, delimiter='\t'):
            if Metapuzzle.objects.filter(name=row["name"]).exists():
                continue
            print("  Metapuzzle \"%s\"..." % row["name"])
            metapuzzle = Metapuzzle.objects.create(**row)
            metapuzzle.save() 
            system_log('load-metapuzzle', 'Loaded metapuzzle "%s"' % metapuzzle.name, object_id=metapuzzle.name)
    print("Done loading metapuzzles")

def load_interactions():
    print("Loading interactions from interactions.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'interactions.txt'), 'r') as team_file:
        for row in csv.DictReader(team_file, delimiter='\t'):
            if Interaction.objects.filter(name=row["name"]).exists():
                continue
            print("  Interaction \"%s\"..." % row["name"])
            interaction = Interaction.objects.create(**row)
            interaction.save() 
            system_log('load-interaction', 'Loaded interaction "%s"' % interaction.name, object_id=interaction.name)
    print("Done loading interactions")

def load_rounds():
    print("Loading rounds from rounds.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'rounds.txt'), 'r') as team_file:
        for row in csv.DictReader(team_file, delimiter='\t'):
            if Round.objects.filter(url=row["url"]).exists():
                continue
            print("  Round \"%s\"..." % row["name"])
            round = Round.objects.create(**row)
            round.save() 
            system_log('load-round', 'Loaded round "%s"' % round.name, object_id=round.url)
    print("Done loading rounds")

def load_puzzles():
    print("Loading puzzles from puzzles.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'puzzles.txt'), 'r') as team_file:
        for row in csv.DictReader(team_file, delimiter='\t'):
            if Puzzle.objects.filter(url=row["url"]).exists():
                continue
            print("  Puzzle \"%s\"..." % row["name"])
            row["round"] = Round.objects.get(url=row["round"])
            puzzle = Puzzle.objects.create(**row)
            puzzle.save() 
            system_log('load-puzzle', 'Loaded puzzle "%s" into round "%s"' % (puzzle.name, puzzle.round.name), object_id=puzzle.url)
    print("Done loading puzzles")

def load_teams():
    print("Loading teams from teams.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'teams.txt'), 'r') as team_file:
        for row in csv.DictReader(team_file, delimiter='\t'):
            if Team.objects.filter(url=row["url"]).exists():
                continue
            print("  Team \"%s\"..." % row["name"])
            team = Team.objects.create(**row)
            team.save() 
            system_log('load-team', 'Loaded team "%s"' % team.name, object_id=team.url)
            # 2014-specific:
            initial_rounds = [Round.objects.get(url='mit'), Round.objects.get(url='events')]
            for initial_round in initial_rounds:
                RoundAccess.objects.create(team=team, round=initial_round).save()
                team_log_round_access(team, initial_round, "The hunt begins")
            teamdata = Y2014TeamData.objects.create(team=team)
            teamdata.save()
            for mitdata in Y2014MitPuzzleData.objects.all():
                if mitdata.location.start:
                    PuzzleAccess.objects.create(team=team, puzzle=mitdata.puzzle).save()
                    team_log_puzzle_access(team, mitdata.puzzle, "The hunt begins")
    print("Done loading teams")

def load_team_phones():
    print("Loading team phones from team_phones.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'team_phones.txt'), 'r') as team_file:
        for row in csv.DictReader(team_file, delimiter='\t'):
            try:
                team = Team.objects.get(url=row["team"])
            except:
                print('ERROR: no such node "%s"' % row["node1"])
                continue
            TeamPhone.objects.filter(phone=row["phone"]).delete()
            TeamPhone.objects.create(team=team, phone=row["phone"]).save()
    print("Done loading team phones")

def load_mit_nodes(): # 2014-specific
    print("Loading mit map nodes from mit_nodes.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'mit_nodes.txt'), 'r') as node_file:
        for row in csv.DictReader(node_file, delimiter='\t'):
            Y2014MitMapNode.objects.filter(name=row["name"]).delete()
            row['start'] = (row['start'] == 'yes')
            mitnode = Y2014MitMapNode.objects.create(**row)
            mitnode.save()
    print("Done loading mit nodes")

def load_mit_edges(): # 2014-specific
    print("Loading mit map edges from mit_edges.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'mit_edges.txt'), 'r') as edge_file:
        for row in csv.DictReader(edge_file, delimiter='\t'):
            try:
                node1 = Y2014MitMapNode.objects.get(name=row["node1"])
            except:
                print('ERROR: no such node "%s"' % row["node1"])
                continue
            try:
                node2 = Y2014MitMapNode.objects.get(name=row["node2"])
            except:
                print('ERROR: no such node "%s"' % row["node2"])
                continue
            Y2014MitMapEdge.objects.filter(node1=node1, node2=node2).delete()
            mitedge = Y2014MitMapEdge.objects.create(node1=node1, node2=node2)
            mitedge.save()
    print("Done loading mit edges")

def load_mit_data(): # 2014-specific
    print("Loading mit data from mit_data.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'mit_data.txt'), 'r') as data_file:
        for row in csv.DictReader(data_file, delimiter='\t'):
            try:
                location = Y2014MitMapNode.objects.get(name=row["location"])
            except:
                print('ERROR: no such puzzle "%s"' % row["url"])
                continue
            try:
                puzzle = Puzzle.objects.get(url=row["url"])
            except:
                print('ERROR: no such puzzle "%s"' % row["url"])
                continue
            if puzzle.round.url != "mit":
                print('ERROR: puzzle "%s" isn\'t in round "mit"' % row["url"])
                continue
            Y2014MitPuzzleData.objects.filter(card=row["card"]).delete()
            Y2014MitPuzzleData.objects.filter(location=location).delete()
            Y2014MitPuzzleData.objects.filter(puzzle=puzzle).delete()
            mitdata = Y2014MitPuzzleData.objects.create(puzzle=puzzle, card=row["card"], location=location)
            mitdata.save()
    print("Done loading mit data")


def load_caucus_data(): # 2014-specific
    print("Loading caucus data from caucus_data.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'caucus_data.txt'), 'r') as data_file:
        for row in csv.DictReader(data_file, delimiter='\t'):
            if Y2014CaucusAnswerData.objects.filter(bird=row["bird"]).exists():
                continue
            Y2014CaucusAnswerData.objects.create(**row).save()
    print("Done loading caucus data")

def load_knights_data(): # 2014-specific
    print("Loading knights data from knights_data.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'knights_data.txt'), 'r') as data_file:
        for row in csv.DictReader(data_file, delimiter='\t'):
            if Y2014KnightsAnswerData.objects.filter(piece=row["piece"], order=row["order"]).exists():
                continue
            Y2014KnightsAnswerData.objects.create(**row).save()
    print("Done loading knights data")

def load_all_inner():
    load_metapuzzles()
    load_interactions()
    load_rounds()
    load_puzzles()
    load_mit_nodes() # 2014-specific
    load_mit_edges() # 2014-specific / must load after mit_nodes
    load_mit_data() # 2014-specific / must load after mit_nodes and puzzles, and must load before teams
    load_caucus_data() # 2014-specific
    load_knights_data() # 2014-specific
    load_teams()
    load_team_phones()

def load_all():
    try:
        from django.db import transaction # Django 1.6 required here
        with transaction.atomic():
            load_all_inner();
    except:
        load_all_inner();


def everybody_can_see_everything_inner():
    print("Granting full access to every team...")
    for team in Team.objects.all():
        td = Y2014TeamData.objects.get(team=team)
        td.humpty_pieces = 12
        td.save()
        for round in Round.objects.all():
            if not RoundAccess.objects.filter(team=team, round=round).exists():
                RoundAccess.objects.create(team=team, round=round).save()
        for puzzle in Puzzle.objects.all():
            if not PuzzleAccess.objects.filter(team=team, puzzle=puzzle).exists():
                PuzzleAccess.objects.create(team=team, puzzle=puzzle).save()
        for metapuzzle in Metapuzzle.objects.all():
            if not MetapuzzleSolve.objects.filter(team=team, metapuzzle=metapuzzle).exists():
                MetapuzzleSolve.objects.create(team=team, metapuzzle=metapuzzle).save()
    print("Done granting full access")

def everybody_can_see_everything():
    try:
        from django.db import transaction # Django 1.6 required here
        with transaction.atomic():
            everybody_can_see_everything_inner();
    except:
        everybody_can_see_everything_inner();
