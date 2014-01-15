from django.conf import settings
from django.template import Template, Context

import platform
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
    logger.info('Writing htpasswd file...')
    try:
        with open(settings.HTPASSWD_FILE, 'w') as htpasswd_file:
            for team in Team.objects.all():
                salt = random.choice(saltchars) + random.choice(saltchars)
                htpasswd_file.write('%s:%s\n' % (team.username, crypt.crypt(team.password, salt)))
    except IOError as e:
        logger.exception('Failed to write htpasswd file %s, IT MAY BE IN AN INVALID STATE', settings.HTPASSWD_FILE)
        raise e
    logger.info('Done writing htpasswd file')

def prestart_team(team, suffix=None):
    team_path = team.get_team_dir(suffix)
    user_symlink = team.get_user_symlink()
    if not os.path.exists(team_path):
        try:
            os.mkdir(team_path)
            with open(os.path.join(team_path, '.team-dir-marker'), 'a'):
                pass
        except:
            logger.exception('Failed to create team directory %s', team_path)
            return False
    if platform.system() != 'Windows' and not os.path.lexists(user_symlink):
        try:
            os.symlink(team.get_team_dir(), user_symlink)
        except:
            logger.exception('Failed to create symlink at %s to %s', user_symlink, team.get_team_dir())
    try:
        team_htaccess_path = os.path.join(team_path, '.htaccess')
        with open(team_htaccess_path, 'w') as htaccess_file:
            htaccess_file.write('''AuthType Basic
AuthName "Mystery Hunt"
AuthUserFile %s
Require User %s''' % (settings.HTPASSWD_FILE, team.username))
            htaccess_file.close()
    except:
        logger.exception('Failed to initialize team directory %s, IT MAY BE IN AN INVALID STATE', team_path)
        raise e
    return True

def prestart_all():
    teams = Team.objects.all()
    logger.info('Prestarting hunt for %d teams...', len(teams))
    for team in teams:
        logger.info('  Team "%s"...', team.url)
        prestart_team(team)
    logger.info('Done prestarting hunt')

def start_team(team):
    # TODO: insert mh2014 start logic here
    pass

def start_all():
    teams = Team.objects.all()
    logger.info('Starting hunt for %d teams...', len(teams))
    for team in teams:
        logger.info('  Team "%s"...', team.url)
        start_team(team)
    logger.info('Done starting hunt')

log_entry_protect = re.compile(r"\[\[([^\]]*)\]\]")

class TopContext(Context):
    def __init__(self, team):
        Context.__init__(self)
        self['team'] = team
        self['rounds'] = [self.round_obj(x) for x in RoundAccess.objects.filter(team=team).order_by('id')]
        self['solved_metas'] = [x.metapuzzle for x in MetapuzzleSolve.objects.filter(team=team).order_by('id')]
        self['log_entries'] = [{"entry": x} for x in TeamLog.objects.filter(team=team).order_by('-id')]
        for entry in self['log_entries']:
            msg = entry['entry'].message
            if "[[" in msg:
                entry['protected_message'] = log_entry_protect.sub('[hidden]', msg)
                entry['unprotected_message'] = log_entry_protect.sub(r'\1', msg)
        # ----- 2014-specific -----
        self['has_wl_access'] = (len(self['rounds']) > 2)
        try:
            self['gone_with_the_wind_released'] = PuzzleAccess.objects.filter(team=team, puzzle=Puzzle.objects.get(url='gone_with_the_wind')).exists()
        except:
            logger.exception('couldn\'t determine if gone_with_the_wind has been released')
            pass
        self['team_data'] = Y2014TeamData.objects.get(team=team)
        points = self['team_data'].points
        self['tickett'] = TRAIN_COST
        if points >= TRAIN_READY[2]:
            self['ticket'] = 0
            self['tickett'] = None
        elif points < DRINK_READY[-1]:
            self['ticket'] = 0
        elif points >= TRAIN_READY[1]:
            self['ticket'] = min(TRAIN_COST, max(0, points - TRAIN_READY[1]))
        elif points >= TRAIN_READY[0]:
            self['ticket'] = min(TRAIN_COST, max(0, points - TRAIN_READY[0]))
        else:
            self['ticket'] = min(TRAIN_COST, max(0, points - DRINK_READY[-1]))
        self['ticketx'] = self['ticket']*10/TRAIN_COST
    def round_obj(self, access):
        ret = {"round": access.round}
        if access.round.url == 'mit':
            if MetapuzzleSolve.objects.filter(team=access.team, metapuzzle__url='jabberwock').exists():
                ret["solved"] = True
        else:
            if MetapuzzleSolve.objects.filter(team=access.team, metapuzzle__url=access.round.url).exists():
                ret["solved"] = True
        ret["puzzles"] = [self.puzzle_obj(x) for x in PuzzleAccess.objects.filter(puzzle__round=access.round, team=access.team).order_by('id')]
        return ret
    def puzzle_obj(self, access):
        ret = {"puzzle": access.puzzle, "solved": access.solved}
        if access.puzzle.round.url == 'mit': # 2014-specific
            try:
                d = Y2014MitPuzzleData.objects.get(puzzle=access.puzzle)
                ret["card"] = d.card
            except:
                logger.exception('puzzle "%s" doesn\'t have a card assigned', access.puzzle.url)
        if access.puzzle.round.url == 'tea_party': # 2014-specific
            data = Y2014PartyAnswerData.objects.get(answer=access.puzzle.answer)
            if data.type1 == 'cup':
                ret["cup"] = data.type2
            else:
                ret["chair"] = data.type2
        return ret

class RoundContext(TopContext): # todo don't inherit, it'll just slow things down and we don't need all that context
    def __init__(self, team, round):
        TopContext.__init__(self, team)
        try:
            team.rounds.get(url=round.url)
        except:
            logger.exception('team "%s" doesn\'t have access to round "%s"', team.url, round.url)
            return
        self['round'] = self.round_obj(RoundAccess.objects.get(team=team, round=round))
        self['puzzles'] = self['round']['puzzles']
        if MetapuzzleSolve.objects.filter(metapuzzle__url=round.url, team=team).exists(): # 2014-specific
            self['round']['solved'] = True
        if round.url == 'mit': # 2014-specific
            count = 0
            for x in self['solved_metas']:
                if x.url in ['spades', 'clubs', 'diamonds']:
                    count = count + 1
            self['bait_ready'] = count < 3
            count = 0
            for x in self['rounds']:
                if x['round'].url in ["tea_party", "mock_turtle", "white_queen"]:
                    count = count + 1
            points = self['team_data'].points
            self['vial1'] = self['vial2'] = self['vial3'] = -1
            self['vial1t'] = DRINK_COST[0]
            self['vial2t'] = DRINK_COST[1]
            self['vial3t'] = DRINK_COST[2]
            if count < 3:
                self['vial3'] = min(DRINK_COST[2],max(0, points - DRINK_READY[1]))
                self['vial3x'] = self['vial3']*10/DRINK_COST[2]
            if count < 2:
                self['vial2'] = min(DRINK_COST[1],max(0, points - DRINK_READY[0]))
                self['vial2x'] = self['vial2']*10/DRINK_COST[1]
            if count < 1:
                self['vial1'] = min(DRINK_COST[0],max(0, points))
                self['vial1x'] = self['vial1']*10/DRINK_COST[0]
            if InteractionAccess.objects.filter(team=team, interaction__url='mit_runaround', accomplished=True).exists():
                if MetapuzzleSolve.objects.filter(team=team, metapuzzle__url='jabberwock').exists():
                    self['meta_status'] = 'solved'
                else:
                    self['meta_status'] = 'solving'
            elif InteractionAccess.objects.filter(team=team, interaction__url='mit_runaround', accomplished=False).exists():
                self['meta_status'] = 'runaround'
            elif InteractionAccess.objects.filter(team=team, interaction__url='mit_runaround_start', accomplished=False).exists():
                self['meta_status'] = 'runaround_start'
        if round.url == 'events': # 2014-specific
            solves = 0
            for i in range(len(self['puzzles'])):
                self['puzzle_'+str(i)] = self['puzzles'][i]
                if self['puzzles'][i]['solved']:
                    solves += 1
            self['meta_ready'] = solves == 4
        if round.url == 'caucus_race': # 2014-specific
            birds = []
            for bird in Y2014CaucusAnswerData.objects.all():
                yes_solved = False
                no_solved = False
                try:
                    yes_puzzle = Puzzle.objects.get(round=round, answer=bird.yes_answer)
                    yes_solved = PuzzleAccess.objects.get(puzzle=yes_puzzle, team=team).solved
                except:
                    yes_puzzle = None
                    pass
                try:
                    no_puzzle = Puzzle.objects.get(round=round, answer=bird.no_answer)
                    no_solved = PuzzleAccess.objects.get(puzzle=no_puzzle, team=team).solved
                except:
                    no_puzzle = None
                    pass
                birds.append({
                    "yes": yes_puzzle, 
                    "yes_solved": yes_solved,
                    "no": no_puzzle,
                    "no_solved": no_solved,
                })
            self['birds'] = birds
        if round.url == 'white_queen': # 2014-specific
            self['herring_ok'] = InteractionAccess.objects.filter(team=team, interaction__url='white_queen_gift', accomplished=True).exists()
            pwa = 'puzzle_with_answer_'
            answers_tmp = ['WILLIAMS', None, 'LYNN', None, None, None, None, None, 'SULLIVAN', None, None, None, None, None, 'SULLIVAN', None, 'RICE', None]
            meta_urls = [None for i in range(18)]
            for meta in Metapuzzle.objects.all():
                if meta.url.startswith('white_queen_a'):
                    for i in range(18):
                        if answers_tmp[i] is None:
                            answers_tmp[i] = meta.answer
                            meta_urls[i] = meta.url
                            break
            answers = []
            urls = []
            for answer in answers_tmp:
                if answer in answers:
                    urls.append('another_'+pwa+answer.lower().replace(' ','_'))
                else:
                    urls.append(pwa+answer.lower().replace(' ','_'))
                answers.append(answer)
            letters = 'ITSJUSTAREDHERRING'
            self['rows'] = [r for r in range(6)]
            self['columns'] = [c for c in range(3)]
            cells = [];
            for r in range(6):
                for c in range(3):
                    answer = None
                    url = None
                    solved = False
                    if PuzzleAccess.objects.filter(team=team, puzzle__url=urls[r*3+c]).exists():
                        answer = answers[r*3+c]
                        url = urls[r*3+c]
                        solved = PuzzleAccess.objects.get(team=team, puzzle__url=urls[r*3+c]).solved
                    cells.append({
                        'row': r+1,
                        'column': c+1,
                        'letter': letters[r*3+c],
                        'answer': answer,
                        'solved': solved,
                        'url': url,
                        'meta_url': meta_urls[r*3+c]
                        });
            self['cells'] = cells
        if round.url == "humpty_dumpty": # 2014-specific
            jigsaw = Y2014TeamData.objects.get(team=team).humpty_pieces
            self['jigsaw'] = jigsaw

class PuzzleContext(RoundContext): # todo don't inherit, it'll just slow things down and we don't need all that context
    def __init__(self, team, puzzle):
        try:
            round = team.rounds.get(url=puzzle.round.url)
        except:
            logger.exception('team "%s" doesn\'t have access to round "%s"', team.url, puzzle.round.url)
            TopContext.__init__(self, team)
            return
        RoundContext.__init__(self, team, round)
        try:
            team.puzzles.get(url=puzzle.url)
        except:
            logger.exception('team "%s" doesn\'t have access to puzzle "%s"', team.url, puzzle.url)
            return
        self['puzzle'] = self.puzzle_obj(PuzzleAccess.objects.get(team=team, puzzle=puzzle))
        if puzzle.url == 'puzzle_with_answer_garciaparra': # 2014-specific
            self['stage3'] = InteractionAccess.objects.filter(team=team, interaction__url='pwa_garciaparra_food', accomplished=True).exists()
            self['stage2'] = InteractionAccess.objects.filter(team=team, interaction__url='pwa_garciaparra_url', accomplished=True).exists()
            if self['stage2']:
                try:
                    self['stage2url'] = Y2014PwaGarciaparraUrlSubmission.objects.filter(team=team).order_by('-id')[0].url
                except:
                    self['stage2url'] = '???'

def publish_dir(context, source_path, dest_path, root_path, except_for=[]):
    for dirpath, dirnames, filenames in os.walk(source_path):
        relpath = os.path.relpath(dirpath, source_path)
        if relpath in except_for:
            continue
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
                    except:
                        logger.exception('error running template "%s"', os.path.abspath(source_file))
                        continue
                    with open(dest_file, 'w') as file_out:
                        file_out.write(result)
            else:
                dest_file = os.path.join(dest_path, relpath, filename)
                if not os.path.exists(dest_file) or os.path.getmtime(dest_file) < os.path.getmtime(source_file):
                    if platform.system() == 'Windows':
                        try:
                            shutil.copyfile(source_file, dest_file)
                        except:
                            logger.exception('Failed to copy %s to %s', source_file, dest_file)
                    else:
                        try:
                            os.symlink(source_file, os.path.abspath(dest_file))
                        except:
                            logger.exception('Failed to create symlink at %s to %s', dest_file, source_file)
        for dirname in dirnames:
            if relpath == '.' and dirname in except_for:
                continue
            dest_dir = os.path.join(dest_path, relpath, dirname)
            if not os.path.isdir(dest_dir):
                try:
                    os.mkdir(dest_dir)
                except:
                    logger.exception('can\'t create directory "%s": %s', os.path.abspath(dest_dir))
                    continue

def ensure_team_dir(team, suffix=None):
    team_path = team.get_team_dir(suffix)
    if not os.path.exists(team_path):
        return prestart_team(team, suffix)
    return True

def publish_team_top(team, suffix=None):
    logger.info("publish %s/top", team.url)
    if not ensure_team_dir(team, suffix):
        return
    team_path = team.get_team_dir(suffix)
    top_context = TopContext(team)
    except_for = []
    if not top_context["has_wl_access"]: # 2014-specific
        except_for = ['wonderland']
    publish_dir(top_context, os.path.join(settings.HUNT_DATA_DIR, 'top'), team_path, '.', except_for)

def publish_team_round(team, round, suffix=None):
    logger.info("publish %s/round/%s", team.url, round.url)
    if not ensure_team_dir(team, suffix):
        return
    team_path = team.get_team_dir(suffix)
    round_dir = os.path.join(team_path, 'round', round.url)
    if not os.path.isdir(os.path.abspath(round_dir)):
        try:
            os.makedirs(os.path.abspath(round_dir))
        except:
            logger.exception('couldn\'t create directory "%s"', round_dir)
            return
    round_context = RoundContext(team, round)
    publish_dir(round_context, os.path.join(settings.HUNT_DATA_DIR, 'round', round.url, 'round'), round_dir, '../..')
    # --- 2014-specific ---
    if team.url == 'hunt_hq':
        solution_context = RoundContext(team, round)
        solution_context['name'] = round.name
        solution_context['url'] = 'round/' + round.url
        solution_source = os.path.join(settings.HUNT_DATA_DIR, 'round-solution', round.url)
        if os.path.isdir(solution_source):
            logger.info("  and solution")
            solution_dir = os.path.join(team_path, 'round-solution', round.url)
            if not os.path.isdir(os.path.abspath(solution_dir)):
                try:
                    os.makedirs(os.path.abspath(solution_dir))
                except:
                    logger.exception('couldn\'t create directory "%s"', solution_dir)
                    return
            publish_dir(solution_context, solution_source, solution_dir, '../..', ['index.html', 'solution.css'])
            try:
                with open(os.path.join(solution_source, 'index.html'), 'r') as index_html_file:
                    solution_context['index_html'] = index_html_file.read()
            except:
                logger.exception('couldn\'t read solution html for round %s', round.url)
                return
            if os.path.isfile(os.path.join(solution_source, 'solution.css')):
                with open(os.path.join(solution_source, 'solution.css'), 'r') as solution_css_file:
                    solution_context['solution_css'] = solution_css_file.read()
            publish_dir(solution_context, os.path.join(settings.HUNT_DATA_DIR, 'round', round.url, 'solution'), solution_dir, '../..')
        else:
            logger.warning('no solution for round %s', round.url)
    if round.url == 'humpty_dumpty':
        jigsaw = Y2014TeamData.objects.get(team=team).humpty_pieces
        if not os.path.isdir(os.path.join(round_dir, 'jigsaw')):
            try:
                os.makedirs(os.path.join(round_dir, 'jigsaw'))
            except:
                logger.exception("couldn't create directory %s", os.path.join(round_dir, 'jigsaw'))
        if os.path.isdir(os.path.join(round_dir, 'jigsaw')):
            for i in range(1,jigsaw+1):
                try:
                    source_file = os.path.join(settings.HUNT_DATA_DIR, 'round', round.url, 'jigsaw', "%02d.png" % i)
                    dest_file = os.path.join(round_dir, 'jigsaw', "%02d.png" % i)
                    shutil.copyfile(source_file, dest_file)
                    source_file = os.path.join(settings.HUNT_DATA_DIR, 'round', round.url, 'jigsaw', "%02d-thumb.png" % i)
                    dest_file = os.path.join(round_dir, 'jigsaw', "%02d-thumb.png" % i)
                    shutil.copyfile(source_file, dest_file)
                except:
                    logger.exception('couldn\'t copy jigsaw piece %d', i)

def publish_team_puzzle(team, puzzle, suffix=None):
    logger.info("publish %s/puzzle/%s", team.url, puzzle.url)
    if not ensure_team_dir(team, suffix):
        return
    team_path = team.get_team_dir(suffix)
    puzzle_dir = os.path.join(team_path, 'puzzle', puzzle.url)
    if not os.path.isdir(os.path.abspath(puzzle_dir)):
        try:
            os.makedirs(os.path.abspath(puzzle_dir))
        except:
            logger.exception('couldn\'t create directory "%s"', puzzle_dir)
            return
    puzzle_context = PuzzleContext(team, puzzle)
    puzzle_source = os.path.join(settings.HUNT_DATA_DIR, 'puzzle', puzzle.url)
    except_for = ['index.html', 'index.html.tmpl', 'puzzle.css', 'puzzle.js']
    if puzzle.url == 'puzzle_with_answer_garciaparra': # 2014-specific
        if not puzzle_context['stage2']:
            except_for.append('stage2')
        if not puzzle_context['stage3']:
            except_for.append('stage3')
    publish_dir(puzzle_context, puzzle_source, puzzle_dir, '../..', except_for)
    try:
        html_path = os.path.join(puzzle_source, 'index.html')
        if os.path.isfile(html_path):
            with open(html_path, 'r') as index_html_file:
                puzzle_context['index_html'] = index_html_file.read()
        elif os.path.isfile(html_path+'.tmpl'):
            with open(html_path+'.tmpl', 'r') as index_html_file:
                puzzle_context['index_html'] = Template(index_html_file.read()).render(puzzle_context)
    except:
        logger.exception('couldn\'t read puzzle html for puzzle %s', puzzle.url)
        return
    if os.path.isfile(os.path.join(puzzle_source, 'puzzle.css')):
        with open(os.path.join(puzzle_source, 'puzzle.css'), 'r') as puzzle_css_file:
            puzzle_context['puzzle_css'] = puzzle_css_file.read()
    if os.path.isfile(os.path.join(puzzle_source, 'puzzle.js')):
        with open(os.path.join(puzzle_source, 'puzzle.js'), 'r') as puzzle_js_file:
            puzzle_context['puzzle_js'] = puzzle_js_file.read()
    publish_dir(puzzle_context, os.path.join(settings.HUNT_DATA_DIR, 'round', puzzle.round.url, 'puzzle'), puzzle_dir, '../..')
    # --- 2014-specific ---
    if team.url == 'hunt_hq':
        solution_context = PuzzleContext(team, puzzle)
        solution_context['name'] = puzzle.name + ' (' + puzzle.round.name + ')'
        solution_context['url'] = 'puzzle/' + puzzle.url
        solution_source = os.path.join(settings.HUNT_DATA_DIR, 'puzzle-solution', puzzle.url)
        if os.path.isdir(solution_source):
            logger.info("  and solution")
            solution_dir = os.path.join(team_path, 'puzzle-solution', puzzle.url)
            if not os.path.isdir(os.path.abspath(solution_dir)):
                try:
                    os.makedirs(os.path.abspath(solution_dir))
                except:
                    logger.exception('couldn\'t create directory "%s"', solution_dir)
                    return
            publish_dir(solution_context, solution_source, solution_dir, '../..', ['index.html', 'solution.css'])
            try:
                with open(os.path.join(solution_source, 'index.html'), 'r') as index_html_file:
                    solution_context['index_html'] = index_html_file.read()
            except:
                logger.exception('couldn\'t read solution html for puzzle %s', puzzle.url)
                return
            if os.path.isfile(os.path.join(solution_source, 'solution.css')):
                with open(os.path.join(solution_source, 'solution.css'), 'r') as solution_css_file:
                    solution_context['solution_css'] = solution_css_file.read()
            publish_dir(solution_context, os.path.join(settings.HUNT_DATA_DIR, 'round', puzzle.round.url, 'solution'), solution_dir, '../..')
        else:
            logger.warning('no solution for puzzle %s', puzzle.url)
    if puzzle.round.url == 'mit':
        try:
            card = Y2014MitPuzzleData.objects.get(puzzle=puzzle).card
            source_file = os.path.join(settings.HUNT_DATA_DIR, 'round', 'mit', 'cards', card.name+'.png')
            dest_file = os.path.join(puzzle_dir, 'card.png')
            shutil.copyfile(source_file, dest_file)
            source_file = os.path.join(settings.HUNT_DATA_DIR, 'round', 'mit', 'edges', card.name+'.png')
            dest_file = os.path.join(puzzle_dir, 'paths.png')
            shutil.copyfile(source_file, dest_file)
        except:
            logger.exception('puzzle "%s" doesn\'t have a card assigned', puzzle.url)
    if puzzle.round.url == 'knights':
        try:
            data = Y2014KnightsAnswerData.objects.get(answer=puzzle.answer)
            source_file = os.path.join(settings.HUNT_DATA_DIR, 'round', 'knights', 'pieces', data.color+'_'+data.piece+'.png')
            dest_file = os.path.join(puzzle_dir, 'piece.png')
            shutil.copyfile(source_file, dest_file)
        except:
            logger.exception('puzzle "%s" doesn\'t have a chess piece assigned', puzzle.url)


def publish_team(team, suffix=None):
    publish_team_top(team, suffix)
    for round in team.rounds.all():
        publish_team_round(team, round, suffix)
    for puzzle in team.puzzles.all():
        publish_team_puzzle(team, puzzle, suffix)

def publish_all():
    teams = Team.objects.all()
    logger.info('Publishing hunt for %d teams...', len(teams))
    for team in teams:
        publish_team(team)
    logger.info('Done publishing hunt')

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
    except:
        logger.exception('Failed to remove "%s"', team_path)
        return
    last_error = None
    for i in range(1,5):
        try:
            os.rename(team_path_new, team_path)
            return
        except:
            if i == 1:
                logger.warning('couldn\'t move "%s" to "%s", trying again...', team_path_new, team_path, exc_info=True)
            last_error = sys.exc_info()
            time.sleep(i)
    logger.error('Failed to move "%s" to "%s"', team_path_new, team_path, exc_info=last_error)

def republish_team(team):
    republish_team_start(team)
    republish_team_finish(team)

def republish_all():
    publish_htpasswd()
    teams = Team.objects.all()
    logger.info('Republishing hunt for %d teams...', len(teams))
    for team in teams:
        logger.info('  Start Team "%s"...', team.url)
        republish_team_start(team)
    for team in teams:
        logger.info('  Finish Team "%s"...', team.url)
        republish_team_finish(team)
    logger.info('Done republishing hunt')
