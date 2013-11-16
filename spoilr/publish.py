from django.conf import settings
from django.template import Template, Context

import time
import logging
import os
import shutil
from .models import *

logger = logging.getLogger(__name__)

def prestart_team(team, suffix=None):
    team_path = team.get_path(suffix)
    if not os.path.exists(team_path):
        try:
            os.mkdir(team_path)
            with open(os.path.join(team_path, '.team-dir-marker'), 'a'):
                pass
        except OSError as e:
            logger.error('Failed to create team directory %s: %s', team_path, str(e))
            return False
    try:
        team_htaccess_path = os.path.join(team_path, '.htaccess')
        with open(team_htaccess_path, 'w') as htaccess_file:
            htaccess_file.write('''AuthType Basic
AuthName "Mystery Hunt"
AuthUserFile %s
Require User %s''' % (settings.HTPASSWD_FILE, team.username))
            htaccess_file.close()
    except IOError as e:
        logger.error('Failed to initialize team directory %s, IT MAY BE IN AN INVALID STATE: %s', team_path, str(e))
        raise e
    return True

def prestart_all():
    teams = Team.objects.all()
    print('Prestarting hunt for %d teams...' % len(teams))
    for team in teams:
        print('  Team "%s"...' % team.url)
        prestart_team(team)
    print('Done prestarting hunt')

def start_team(team):
    # TODO: insert mh2014 start logic here
    pass

def start_all():
    teams = Team.objects.all()
    print('Starting hunt for %d teams...' % len(teams))
    for team in teams:
        print('  Team "%s"...' % team.url)
        start_team(team)
    print('Done starting hunt')

class TopContext(Context):
    def __init__(self, team):
        Context.__init__(self)
        self['team'] = team
        rounds = []
        for round in team.rounds.all():
            round_puzzles = [x.puzzle for x in PuzzleAccess.objects.filter(puzzle__round=round,team=team).order_by('puzzle__order')]
            rounds.append({"round": round, "puzzles": round_puzzles})
        self['rounds'] = rounds

class RoundContext(TopContext):
    def __init__(self, team, round):
        TopContext.__init__(self, team)
        try:
            team.rounds.get(url=round.url)
        except:
            logger.error('[bug] team "%s" doesn\'t have access to round "%s"', team.url, round.url)
            return
        self['round'] = round
        self['puzzles'] = [x.puzzle for x in PuzzleAccess.objects.filter(puzzle__round=round,team=team).order_by('puzzle__order')]

class PuzzleContext(RoundContext):
    def __init__(self, team, puzzle):
        try:
            round = team.rounds.get(url=puzzle.round.url)
        except:
            logger.error('[bug] team "%s" doesn\'t have access to round "%s"', team.url, round.url)
            TopContext.__init__(self, team)
            return
        RoundContext.__init__(self, team, round)
        try:
            team.puzzles.get(url=puzzle.url)
        except:
            logger.error('[bug] team "%s" doesn\'t have access to puzzle "%s"', team.url, puzzle.url)
            return
        self['puzzle'] = puzzle
        self['round'] = round

def publish_dir(context, source_path, dest_path, root_path, except_for=[]):
    for dirpath, dirnames, filenames in os.walk(source_path):
        relpath = os.path.relpath(dirpath, source_path)
        context['root'] = os.path.relpath(root_path, relpath).replace('\\','/')
        for filename in filenames:
            if relpath == '.' and filename in except_for:
                continue
            source_file = os.path.join(dirpath, filename)
            if filename[-5:] == '.tmpl':
                dest_file = os.path.join(dest_path, relpath, filename[:-5])
                with open(source_file, 'r') as file_in:
                    try:
                        result = Template(file_in.read()).render(context)
                    except Exception as e:
                        logger.error('error running template "%s": %s', os.path.abspath(source_file), str(e))
                        continue
                    with open(dest_file, 'w') as file_out:
                        file_out.write(result)
            else:
                dest_file = os.path.join(dest_path, relpath, filename)
                shutil.copyfile(source_file, dest_file)
        for dirname in dirnames:
            if relpath == '.' and dirname in except_for:
                continue
            dest_dir = os.path.join(dest_path, relpath, dirname)
            try:
                os.mkdir(dest_dir)
            except OSError as e:
                logger.error('can\'t create directory "%s": %s', os.path.abspath(dest_dir), str(e))
                continue

def publish_team(team, suffix=None):
    print('    Top...')
    team_path = team.get_path(suffix)
    if not os.path.exists(team_path):
        if not prestart_team(team, suffix):
            return
    top_context = TopContext(team)
    publish_dir(top_context, os.path.join(settings.HUNT_DATA_DIR, 'top'), team_path, '.')
    for round in team.rounds.all():
        print('    Round %s...' % round.url)
        round_dir = os.path.join(team_path, 'round', round.url)
        try:
            os.makedirs(os.path.abspath(round_dir))
        except OSError as e:
            logger.error('couldn\'t create directory "%s": %s', round_dir, str(e))
            continue
        round_context = RoundContext(team, round)
        publish_dir(round_context, os.path.join(settings.HUNT_DATA_DIR, 'round', round.url, 'round'), round_dir, '../..')
    for puzzle in team.puzzles.all():
        print('    Puzzle %s...' % puzzle.url)
        puzzle_dir = os.path.join(team_path, 'puzzle', puzzle.url)
        try:
            os.makedirs(os.path.abspath(puzzle_dir))
        except OSError as e:
            logger.error('couldn\'t create directory "%s": %s', puzzle_dir, str(e))
            continue
        puzzle_context = PuzzleContext(team, puzzle)
        puzzle_source = os.path.join(settings.HUNT_DATA_DIR, 'puzzle', puzzle.url)
        publish_dir(puzzle_context, puzzle_source, puzzle_dir, '../..', ['index.html', 'puzzle.css', 'puzzle.js'])
        try:
            with open(os.path.join(puzzle_source, 'index.html'), 'r') as index_html_file:
                puzzle_context['index_html'] = index_html_file.read()
        except Exception as e:
            logger.error('couldn\'t read puzzle html: %s', puzzle_dir, str(e))
            continue
        if os.path.isfile(os.path.join(puzzle_source, 'puzzle.css')):
            with open(os.path.join(puzzle_source, 'puzzle.css'), 'r') as puzzle_css_file:
                puzzle_context['puzzle_css'] = puzzle_css_file.read()
        if os.path.isfile(os.path.join(puzzle_source, 'puzzle.js')):
            with open(os.path.join(puzzle_source, 'puzzle.js'), 'r') as puzzle_js_file:
                puzzle_context['puzzle_js'] = puzzle_js_file.read()
        publish_dir(puzzle_context, os.path.join(settings.HUNT_DATA_DIR, 'round', puzzle.round.url, 'puzzle'), puzzle_dir, '../..')
        # --- 2014-specific ---
        if puzzle.round.url == 'mit':
            try:
                card = Y2014MitPuzzleData.objects.get(puzzle=puzzle).card
                source_file = os.path.join(settings.HUNT_DATA_DIR, 'round', 'mit', 'cards', card+'.png')
                dest_file = os.path.join(puzzle_dir, 'card.png')
                shutil.copyfile(source_file, dest_file)
            except:
                logger.error('puzzle "%s" doesn\'t have a playing card assigned' % puzzle.url)

def publish_all():
    teams = Team.objects.all()
    print('Publishing hunt for %d teams...' % len(teams))
    for team in teams:
        print('  Team "%s"...' % team.url)
        publish_team(team)
    print('Done publishing hunt')

def republish_team_start(team):
    team_path_new = team.get_path(".__new__")
    team_path_old = team.get_path(".__old__")
    team_path = team.get_path()
    if os.path.exists(team_path_new):
        shutil.rmtree(team_path_new)
    publish_team(team, ".__new__")

def republish_team_finish(team):
    team_path_new = team.get_path(".__new__")
    team_path = team.get_path()
    try:
        if os.path.exists(team_path):
            shutil.rmtree(team_path)
    except OSError as e:
        logger.error('Failed to remove "%s": %s', team_path, str(e))
        return
    last_error = None
    for i in range(1,5):
        try:
            os.rename(team_path_new, team_path)
            return
        except OSError as e:
            last_error = e
            time.sleep(i)
    logger.error('Failed to move "%s" to "%s": %s', team_path_new, team_path, str(e))

def republish_team(team):
    republish_team_start(team)
    republish_team_finish(team)

def republish_all():
    teams = Team.objects.all()
    print('Republishing hunt for %d teams...' % len(teams))
    for team in teams:
        print('  Start Team "%s"...' % team.url)
        republish_team_start(team)
    for team in teams:
        print('  Finish Team "%s"...' % team.url)
        republish_team_finish(team)
    print('Done republishing hunt')
