from django.conf import settings

import logging
import csv
import shutil
from .models import *

logger = logging.getLogger(__name__)

def get_team_path(team):
    return os.path.join(settings.TEAMS_DIR, team.url)

def load_rounds():
    print("Loading rounds from rounds.csv...")
    with open(os.path.join(settings.LOAD_DIR, 'rounds.csv'), 'r') as team_file:
        for row in csv.DictReader(team_file, delimiter='\t'):
            if Round.objects.filter(url=row["url"]).exists():
                continue
            print("  Round \"%s\"..." % row["name"])
            round = Round.objects.create(**row)
            round.save() 
    print("Done loading rounds")

def load_puzzles():
    print("Loading puzzles from puzzles.csv...")
    with open(os.path.join(settings.LOAD_DIR, 'puzzles.csv'), 'r') as team_file:
        for row in csv.DictReader(team_file, delimiter='\t'):
            if Puzzle.objects.filter(url=row["url"]).exists():
                continue
            print("  Puzzle \"%s\"..." % row["name"])
            row["round"] = Round.objects.get(url=row["round"])
            puzzle = Puzzle.objects.create(**row)
            puzzle.save() 
    print("Done loading puzzles")

def load_teams():
    print("Loading teams from teams.csv...")
    with open(os.path.join(settings.LOAD_DIR, 'teams.csv'), 'r') as team_file:
        for row in csv.DictReader(team_file, delimiter='\t'):
            if Team.objects.filter(url=row["url"]).exists():
                continue
            print("  Team \"%s\"..." % row["name"])
            team = Team.objects.create(**row)
            team.save() 
    print("Done loading teams")

def load_all():
    load_teams()
    load_rounds()
    load_puzzles()

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
