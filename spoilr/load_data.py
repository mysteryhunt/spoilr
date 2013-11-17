from django.conf import settings

import logging
import csv
import shutil
from .log import *
from .models import *

logger = logging.getLogger(__name__)

def get_team_path(team):
    return os.path.join(settings.TEAMS_DIR, team.url)

def load_rounds():
    print("Loading rounds from rounds.txt...")
    with open(os.path.join(settings.LOAD_DIR, 'rounds.txt'), 'r') as team_file:
        for row in csv.DictReader(team_file, delimiter='\t'):
            if Round.objects.filter(url=row["url"]).exists():
                continue
            print("  Round \"%s\"..." % row["name"])
            round = Round.objects.create(**row)
            round.save() 
            system_log('load_round', 'Loaded round "%s"' % round.name, object_id=round.url)
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
            system_log('load_puzzle', 'Loaded puzzle "%s" into round "%s"' % (puzzle.name, puzzle.round.name), object_id=puzzle.url)
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
            system_log('load_team', 'Loaded team "%s"' % team.name, object_id=team.url)
            # 2014-specific:
            mitround = Round.objects.get(url='mit')
            print("    Granting access to %s" % mitround.name)
            RoundAccess.objects.create(team=team, round=mitround).save()
            team_log(team, ROUND_ACCESS, 'Round "%s" released for hunt start' % mitround.name, object_id=mitround.url, link='/round/%s' % mitround.url)
            teamdata = Y2014TeamData.objects.create(team=team)
            teamdata.save()
            for mitdata in Y2014MitPuzzleData.objects.all():
                if mitdata.location.start:
                    print("    Granting access to %s" % mitdata.puzzle.name)
                    PuzzleAccess.objects.create(team=team, puzzle=mitdata.puzzle).save()
                    team_log(team, PUZZLE_ACCESS, 'Puzzle "%s" released for hunt start' % mitdata.puzzle.name, object_id=mitdata.puzzle.url, link='/puzzle/%s' % mitdata.puzzle.url)
    print("Done loading teams")

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

def load_all():
    load_rounds()
    load_puzzles()
    load_mit_nodes() # 2014-specific
    load_mit_edges() # 2014-specific / must load after mit_nodes
    load_mit_data() # 2014-specific / must load after mit_nodes and puzzles, and must load before teams
    load_teams()

def wipe_database_i_really_mean_it():
    print("Wiping the hunt database...")
    for team in Team.objects.all():
        team_path = get_team_path(team)
        if os.path.isdir(team_path) and os.path.isfile(os.path.join(team_path, '.team-dir-marker')):
            print("  Removing \"%s\"..." % os.path.abspath(team_path))
            shutil.rmtree(team_path)
    Team.objects.all().delete()
    Round.objects.all().delete()
    Puzzle.objects.all().delete()
    Y2014MitPuzzleData.objects.all().delete() # 2014-specific
    print("Done wiping database")

def everybody_can_see_everything():
    print("Granting full access to every team...")
    for team in Team.objects.all():
        for round in Round.objects.all():
            if not RoundAccess.objects.filter(team=team, round=round).exists():
                RoundAccess.objects.create(team=team, round=round).save()
        for puzzle in Puzzle.objects.all():
            if not PuzzleAccess.objects.filter(team=team, puzzle=puzzle).exists():
                PuzzleAccess.objects.create(team=team, puzzle=puzzle).save()
    print("Done granting full access")
