from django.db import models
from django.conf import settings

from datetime import datetime
import os.path

class Round(models.Model):
    url = models.CharField(max_length=50, unique=True, verbose_name="id")
    name = models.CharField(max_length=200, unique=True)
    order = models.IntegerField(unique=True)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        ordering = ['order']

class Metapuzzle(models.Model):
    url = models.CharField(max_length=50, unique=True, verbose_name="id")
    name = models.CharField(max_length=200, unique=True)
    answer = models.CharField(max_length=100)
    order = models.IntegerField(unique=True)

    def __str__(self):
        return '%s' % (self.name)

    class Meta:
        ordering = ['order']

class Puzzle(models.Model):
    round = models.ForeignKey(Round)
    url = models.CharField(max_length=50, unique=True, verbose_name="id")
    name = models.CharField(max_length=200, unique=True)
    answer = models.CharField(max_length=50)
    order = models.IntegerField()

    def __str__(self):
        return '%s (%s)' % (self.name, self.round.name)

    class Meta:
        unique_together = ('round', 'order')
        ordering = ['round__order', 'order']
        order_with_respect_to = 'round'

Round.puzzles = models.ManyToManyField(Puzzle)

class Team(models.Model):
    url = models.CharField(max_length=50, unique=True, verbose_name="id")
    username = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=200)
    rounds = models.ManyToManyField(Round, through='RoundAccess')
    puzzles = models.ManyToManyField(Puzzle, through='PuzzleAccess')

    def get_team_dir(self, suffix=None):
        path = os.path.join(settings.TEAMS_DIR, self.url)
        if suffix:
            path = path + suffix
        return path

    def get_user_symlink(self):
        symlink = os.path.join(settings.USERS_DIR, self.username)
        return symlink

    def __str__(self):
        return '%s' % (self.name)

class TeamPhone(models.Model):
    team = models.ForeignKey(Team)
    phone = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return '%s [%s]' % (self.team.name, self.phone)

Team.phones = models.ManyToManyField(TeamPhone)

class SystemLog(models.Model):
    timestamp = models.DateTimeField(default=datetime.now)
    event_type = models.CharField(max_length=50)
    team = models.ForeignKey(Team, blank=True, null=True)
    object_id = models.CharField(max_length=50, blank=True)
    message = models.CharField(max_length=1000)

    def __str__(self):
        return '%s: %s' % (self.timestamp, self.message)

    class Meta:
        verbose_name_plural = "System log"

class TeamLog(models.Model):
    team = models.ForeignKey(Team)
    timestamp = models.DateTimeField(default=datetime.now)
    event_type = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50, blank=True)
    link = models.CharField(max_length=200, blank=True)
    message = models.CharField(max_length=1000)

    def __str__(self):
        return '[%s] %s: %s' % (self.team, self.timestamp, self.message)

class MetapuzzleSolve(models.Model):
    team = models.ForeignKey(Team)
    metapuzzle = models.ForeignKey(Metapuzzle)

    def __str__(self):
        return '%s has solved %s' % (str(self.team), str(self.metapuzzle))

    class Meta:
        unique_together = ('team', 'metapuzzle')

class RoundAccess(models.Model):
    team = models.ForeignKey(Team)
    round = models.ForeignKey(Round)

    def __str__(self):
        return '%s can see %s' % (str(self.team), str(self.round))

    class Meta:
        unique_together = ('team', 'round')
        verbose_name_plural = 'Round access'

class PuzzleAccess(models.Model):
    team = models.ForeignKey(Team)
    puzzle = models.ForeignKey(Puzzle)
    solved = models.BooleanField(default=False)

    def __str__(self):
        s = 'can see'
        if self.solved:
            s = 'has solved'
        return '%s %s %s' % (str(self.team), s, str(self.puzzle))

    class Meta:
        unique_together = ('team', 'puzzle')
        verbose_name_plural = 'Puzzle access'

class PuzzleSubmission(models.Model):
    team = models.ForeignKey(Team)
    phone = models.CharField(max_length=100)
    puzzle = models.ForeignKey(Puzzle)
    timestamp = models.DateTimeField(default=datetime.now)
    answer = models.CharField(max_length=50)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return '%s: %s submitted for %s' % (str(self.timestamp), str(self.team), str(self.puzzle))

    class Meta:
        ordering = ['-timestamp']

class MetapuzzleSubmission(models.Model):
    team = models.ForeignKey(Team)
    phone = models.CharField(max_length=100)
    metapuzzle = models.ForeignKey(Metapuzzle)
    timestamp = models.DateTimeField(default=datetime.now)
    answer = models.CharField(max_length=50)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return '%s: %s submitted for %s' % (str(self.timestamp), str(self.team), str(self.metapuzzle))

    class Meta:
        ordering = ['-timestamp']
    

# ----------------------- 2014-specific stuff ---------------------

class Y2014TeamData(models.Model):
    team = models.ForeignKey(Team, unique=True)
    points = models.IntegerField(default=0, verbose_name='Points')
    humpty_pieces = models.IntegerField(default=0, verbose_name='Humpty Jigsaw Pieces')

    def __str__(self):
        return '%s (%d)' % (self.team.name, self.points)

    class Meta:
        verbose_name = '2014 team data'
        verbose_name_plural = '2014 team data'

class Y2014MitMapNode(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.IntegerField()
    start = models.BooleanField(default=False, verbose_name="Access Granted at Start of Hunt")

    def __str__(self):
        if self.start:
            return '%s (START)' % (self.name)
        else:
            return '%s' % (self.name)

    class Meta:
        ordering = ['order']
        verbose_name = '2014 MIT map node'
        verbose_name_plural = '2014 MIT map nodes'

class Y2014MitMapEdge(models.Model):
    node1 = models.ForeignKey(Y2014MitMapNode, related_name='+')
    node2 = models.ForeignKey(Y2014MitMapNode, related_name='+')

    def __str__(self):
        return '%s <-> %s' % (self.node1.name, self.node2.name)

    class Meta:
        unique_together = ('node1', 'node2')
        ordering = ['node1__order', 'node2__order']
        verbose_name = '2014 MIT map edge'
        verbose_name_plural = '2014 MIT map edges'

class Y2014MitPuzzleData(models.Model):
    puzzle = models.ForeignKey(Puzzle, unique=True, limit_choices_to = {'round__url': 'mit'})

    CARD_CHOICES = []
    for n in [2,3,4,5,6,7,8,9]: # dormouse
        CARD_CHOICES.append((str(n)+'_spades', str(n)+' of spades (dormouse)'))
    for n in [2,4,5,7,9,'J','Q','K']: # caterpillar
        CARD_CHOICES.append((str(n)+'_clubs', str(n)+' of clubs (caterpillar)'))
    for n in ['A',2,3,4,8,9,10,'J']: # tweedle
        CARD_CHOICES.append((str(n)+'_diamonds', str(n)+' of diamonds (tweedle)'))
    card = models.CharField(max_length=12, choices=CARD_CHOICES, unique=True)
    location = models.ForeignKey(Y2014MitMapNode, unique=True)

    def __str__(self):
        return '%s (%s, %s)' % (self.puzzle.name, self.card, self.location.name)

    def mit_meta(self):
        if 'spades' in self.card:
            return 'dormouse'
        if 'clubs' in self.card:
            return 'caterpillar'
        if 'diamonds' in self.card:
            return 'tweedle'

    class Meta:
        ordering = ['puzzle__order', 'card']
        order_with_respect_to = 'puzzle'
        verbose_name = '2014 MIT puzzle data'
        verbose_name_plural = '2014 MIT puzzle data'

class Y2014MitMetapuzzleSubmission(models.Model):
    team = models.ForeignKey(Team)
    phone = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=datetime.now)
    answer = models.CharField(max_length=50)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return '%s: %s submitted for MIT Bait' % (str(self.timestamp), str(self.team))

    class Meta:
        ordering = ['-timestamp']
        verbose_name = '2014 MIT metapuzzle submission'
        verbose_name_plural = '2014 MIT metapuzzle submissions'

class Y2014CaucusAnswerData(models.Model):
    bird = models.IntegerField(unique=True)
    yes_answer = models.CharField(max_length=50)
    no_answer = models.CharField(max_length=50)

    def __str__(self):
        return 'YES:%s NO:%s' % (self.yes_answer, self.no_answer)

    class Meta:
        ordering = ['bird']
        verbose_name = '2014 Caucus answer data'
        verbose_name_plural = '2014 Caucus answer data'

class Y2014KnightsAnswerData(models.Model):
    PIECE_CHOICES = [('pawn', 'pawn'), ('knight', 'knight'), ('bishop', 'bishop'), ('rook', 'rook'), ('queen', 'queen'), ('king', 'king')]
    piece = models.CharField(max_length=10, choices=PIECE_CHOICES)
    COLOR_CHOICES = [('white', 'white'), ('red', 'red')]
    color = models.CharField(max_length=10, choices=COLOR_CHOICES)
    order = models.IntegerField()
    answer = models.CharField(max_length=50)

    def __str__(self):
        return '%s %s %s' % (self.color, self.piece, self.answer)

    class Meta:
        unique_together = ('piece', 'order')
        ordering = ['piece', 'order']
        verbose_name = '2014 Knights answer data'
        verbose_name_plural = '2014 Knights answer data'

