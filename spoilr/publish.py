from django.conf import settings
from django.template import Template, Context

import time
import logging
import os
import shutil
import string
import random
import re
from .models import *
from .constants import *

logger = logging.getLogger(__name__)

def publish_htpasswd():
    try:
        import crypt
    except ImportError:
        return
    saltchars = string.ascii_letters + string.digits
    print('Writing htpasswd file...')
    try:
        with open(settings.HTPASSWD_FILE, 'w') as htpasswd_file:
            for team in Team.objects.all():
                salt = random.choice(saltchars) + random.choice(saltchars)
                htpasswd_file.write('%s:%s\n' % (team.username, crypt.crypt(team.password, salt)))
    except IOError as e:
        logger.error('Failed to write htpasswd file %s, IT MAY BE IN AN INVALID STATE: %s', settings.HTPASSWD_FILE, str(e))
        raise e
    print('Done writing htpasswd file')

def prestart_team(team, suffix=None):
    team_path = team.get_team_dir(suffix)
    user_symlink = team.get_user_symlink()
    if not os.path.exists(team_path):
        try:
            os.mkdir(team_path)
            with open(os.path.join(team_path, '.team-dir-marker'), 'a'):
                pass
        except OSError as e:
            logger.error('Failed to create team directory %s: %s', team_path, str(e))
            return False
    if not os.path.lexists(user_symlink):
        try:
            os.symlink(team.get_team_dir(), user_symlink)
        except OSError as e:
            logger.error('Failed to create symlink at %s to %s: %s', user_symlink, team.get_team_dir(), str(e))
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

log_entry_protect = re.compile(r"\[\[([^\]]*)\]\]")

class TopContext(Context):
    def __init__(self, team):
        Context.__init__(self)
        self['team'] = team
        self['rounds'] = [self.round_obj(x) for x in RoundAccess.objects.filter(team=team).order_by('round__order')]
        self['solved_metas'] = [x.metapuzzle for x in MetapuzzleSolve.objects.filter(team=team).order_by('metapuzzle__order')]
        self['log_entries'] = [{"entry": x} for x in TeamLog.objects.filter(team=team).order_by('timestamp')]
        for entry in self['log_entries']:
            msg = entry['entry'].message
            if "[[" in msg:
                entry['protected_message'] = log_entry_protect.sub('[hidden]', msg)
                entry['unprotected_message'] = log_entry_protect.sub(r'\1', msg)
        # ----- 2014-specific -----
        self['has_wl_access'] = (len(self['rounds']) > 2)
        self['team_data'] = Y2014TeamData.objects.get(team=team)
    def round_obj(self, access):
        ret = {"round": access.round}
        ret["puzzles"] = [self.puzzle_obj(x) for x in PuzzleAccess.objects.filter(puzzle__round=access.round, team=access.team).order_by('puzzle__order')]
        return ret
    def puzzle_obj(self, access):
        ret = {"puzzle": access.puzzle, "solved": access.solved}
        if access.puzzle.round.url == 'mit': # 2014-specific
            try:
                d = Y2014MitPuzzleData.objects.get(puzzle=access.puzzle)
                ret["location"] = d.location
                ret["card"] = d.card
            except:
                logger.error('puzzle "%s" doesn\'t have a location assigned' % access.puzzle.url)
        return ret

class RoundContext(TopContext): # todo don't inherit, it'll just slow things down and we don't need all that context
    def __init__(self, team, round):
        TopContext.__init__(self, team)
        try:
            team.rounds.get(url=round.url)
        except:
            logger.error('[bug] team "%s" doesn\'t have access to round "%s"', team.url, round.url)
            return
        self['round'] = self.round_obj(RoundAccess.objects.get(team=team, round=round))
        self['puzzles'] = self['round']['puzzles']
        if round.url == 'mit': # 2014-specific
            count = 0
            for x in self['solved_metas']:
                if x.name == "The Dormouse":
                    self['portal1'] = 'visible'
                    count = count + 1
                if x.name == "The Caterpillar":
                    self['portal2'] = 'visible'
                    count = count + 1
                if x.name == "Tweedledee and Tweedledum":
                    self['portal3'] = 'visible'
                    count = count + 1
            self['bait_ready'] = count < 3
            count = 0
            for x in self['rounds']:
                if x['round'].url == "tea_party":
                    self['portal1'] = 'open'
                    count = count + 1
                if x['round'].url == "mock_turtle":
                    self['portal2'] = 'open'
                    count = count + 1
                if x['round'].url == "white_queen":
                    self['portal3'] = 'open'
                    count = count + 1
            points = self['team_data'].drink_points
            self['vial1'] = self['vial2'] = self['vial3'] = -1
            if count < 3:
                self['vial3'] = min(14,max(0, points - (DRINK_COST * 2)))
            if count < 2:
                self['vial2'] = min(14,max(0, points - (DRINK_COST * 1)))
            if count < 1:
                self['vial1'] = min(14,max(0, points - (DRINK_COST * 0)))
            #self['meta_ready'] = (points - 14 - (DRINK_COST * count)) >= 0
        if round.url == 'caucus_race': # 2014-specific
            birds = []
            for bird in Y2014CaucusAnswerData.objects.all():
                try:
                    yes_puzzle = Puzzle.objects.get(round=round, answer=bird.yes_answer)
                    PuzzleAccess.objects.get(puzzle=yes_puzzle, team=team)
                except:
                    yes_puzzle = None
                    pass
                try:
                    no_puzzle = Puzzle.objects.get(round=round, answer=bird.no_answer)
                    PuzzleAccess.objects.get(puzzle=no_puzzle, team=team)
                except:
                    no_puzzle = None
                    pass
                birds.append({"yes": yes_puzzle, "no": no_puzzle})
            self['birds'] = birds
            print(str(birds))
        if round.url == 'knights': # 2014-specific
            pieces = []
            for piece in [x[0] for x in Y2014KnightsAnswerData.PIECE_CHOICES]:
                puzzles = []
                for data in Y2014KnightsAnswerData.objects.filter(piece=piece):
                    try:
                        puzzle = Puzzle.objects.get(round=round, answer=data.answer)
                        PuzzleAccess.objects.get(puzzle=puzzle, team=team)
                        puzzles.append({"puzzle": puzzle, "color": data.color, "piece": piece})
                    except:
                        pass
                if len(puzzles) > 0:
                    pieces.append(puzzles)
            self['pieces'] = pieces
        if round.url == 'white_queen': # 2014-specific
            self['herring_ok'] = MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='white_queen_gift').exists()
            pwa = 'puzzle_with_answer_'
            answers = []
            meta_urls = []
            urls = []
            for meta in Metapuzzle.objects.all():
                if meta.url.startswith('white_queen_a'):
                    if meta.answer in answers:
                        urls.append('another_'+pwa+meta.answer.lower().replace(' ','_'))
                    else:
                        urls.append(pwa+meta.answer.lower().replace(' ','_'))
                    answers.append(meta.answer)
                    meta_urls.append(meta.url)
            letters = 'ITSJUSTAREDHERRING'
            self['rows'] = [r for r in range(6)]
            self['columns'] = [c for c in range(3)]
            cells = [];
            for r in range(6):
                for c in range(3):
                    answer = None
                    url = None
                    if PuzzleAccess.objects.filter(team=team, puzzle__url=urls[r*3+c]).exists():
                        answer = answers[r*3+c]
                        url = urls[r*3+c]
                    cells.append({
                        'row': r+1,
                        'column': c+1,
                        'letter': letters[r*3+c],
                        'answer': answer,
                        'url': url,
                        'meta_url': meta_urls[r*3+c]
                        });
            self['cells'] = cells

class PuzzleContext(RoundContext): # todo don't inherit, it'll just slow things down and we don't need all that context
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
        self['puzzle'] = self.puzzle_obj(PuzzleAccess.objects.get(team=team, puzzle=puzzle))

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
                if not os.path.exists(dest_file) or os.path.getmtime(dest_file) < os.path.getmtime(source_file):
                    try:
                        os.symlink(source_file, os.path.abspath(dest_file))
                    except OSError as e:
                        #logger.error('Failed to create symlink at %s to %s: %s', dest_file, source_file, str(e))
                        shutil.copyfile(source_file, dest_file)
        for dirname in dirnames:
            if relpath == '.' and dirname in except_for:
                continue
            dest_dir = os.path.join(dest_path, relpath, dirname)
            if not os.path.isdir(dest_dir):
                try:
                    os.mkdir(dest_dir)
                except OSError as e:
                    logger.error('can\'t create directory "%s": %s', os.path.abspath(dest_dir), str(e))
                    continue

def ensure_team_dir(team, suffix=None):
    team_path = team.get_team_dir(suffix)
    if not os.path.exists(team_path):
        return prestart_team(team, suffix)
    return True

def publish_team_top(team, suffix=None):
    if not ensure_team_dir(team, suffix):
        return
    team_path = team.get_team_dir(suffix)
    top_context = TopContext(team)
    publish_dir(top_context, os.path.join(settings.HUNT_DATA_DIR, 'top'), team_path, '.')

def publish_team_round(team, round, suffix=None):
    if not ensure_team_dir(team, suffix):
        return
    team_path = team.get_team_dir(suffix)
    round_dir = os.path.join(team_path, 'round', round.url)
    if not os.path.isdir(os.path.abspath(round_dir)):
        try:
            os.makedirs(os.path.abspath(round_dir))
        except OSError as e:
            logger.error('couldn\'t create directory "%s": %s', round_dir, str(e))
            return
    round_context = RoundContext(team, round)
    publish_dir(round_context, os.path.join(settings.HUNT_DATA_DIR, 'round', round.url, 'round'), round_dir, '../..')

def publish_team_puzzle(team, puzzle, suffix=None):
    if not ensure_team_dir(team, suffix):
        return
    team_path = team.get_team_dir(suffix)
    puzzle_dir = os.path.join(team_path, 'puzzle', puzzle.url)
    if not os.path.isdir(os.path.abspath(puzzle_dir)):
        try:
            os.makedirs(os.path.abspath(puzzle_dir))
        except OSError as e:
            logger.error('couldn\'t create directory "%s": %s', puzzle_dir, str(e))
            return
    puzzle_context = PuzzleContext(team, puzzle)
    puzzle_source = os.path.join(settings.HUNT_DATA_DIR, 'puzzle', puzzle.url)
    publish_dir(puzzle_context, puzzle_source, puzzle_dir, '../..', ['index.html', 'puzzle.css', 'puzzle.js'])
    try:
        with open(os.path.join(puzzle_source, 'index.html'), 'r') as index_html_file:
            puzzle_context['index_html'] = index_html_file.read()
    except Exception as e:
        logger.error('couldn\'t read puzzle html: %s', puzzle_dir, str(e))
        return
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

def publish_team(team, suffix=None):
    print('    Top...')
    publish_team_top(team, suffix)
    for round in team.rounds.all():
        print('    Round %s...' % round.url)
        publish_team_round(team, round, suffix)
    for puzzle in team.puzzles.all():
        print('    Puzzle %s...' % puzzle.url)
        publish_team_puzzle(team, puzzle, suffix)

def publish_all():
    teams = Team.objects.all()
    print('Publishing hunt for %d teams...' % len(teams))
    for team in teams:
        print('  Team "%s"...' % team.url)
        publish_team(team)
    print('Done publishing hunt')

def republish_team_start(team):
    team_path_new = team.get_team_dir(".__new__")
    team_path_old = team.get_team_dir(".__old__")
    team_path = team.get_team_dir()
    if os.path.exists(team_path_new):
        shutil.rmtree(team_path_new)
    publish_team(team, ".__new__")

def republish_team_finish(team):
    team_path_new = team.get_team_dir(".__new__")
    team_path = team.get_team_dir()
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
    publish_htpasswd()
    teams = Team.objects.all()
    print('Republishing hunt for %d teams...' % len(teams))
    for team in teams:
        print('  Start Team "%s"...' % team.url)
        republish_team_start(team)
    for team in teams:
        print('  Finish Team "%s"...' % team.url)
        republish_team_finish(team)
    print('Done republishing hunt')
