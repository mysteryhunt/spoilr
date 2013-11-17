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

class Puzzle(models.Model):
    round = models.ForeignKey(Round)
    url = models.CharField(max_length=50, unique=True, verbose_name="id")
    name = models.CharField(max_length=200, unique=True)
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

    def get_path(self, suffix=None):
        path = os.path.join(settings.TEAMS_DIR, self.url)
        if suffix:
            path = path + suffix
        return path

    def __str__(self):
        return '%s' % (self.name)

class RoundAccess(models.Model):
    team = models.ForeignKey(Team)
    round = models.ForeignKey(Round)
    start_time = models.DateTimeField(default=datetime.now)
    solved = models.BooleanField(default=False)

    def __str__(self):
        s = 'can see'
        if self.solved:
            s = 'has solved'
        return '%s %s %s' % (str(self.team), s, str(self.round))

    class Meta:
        unique_together = ('team', 'round')
        verbose_name_plural = 'Round access'

class PuzzleAccess(models.Model):
    team = models.ForeignKey(Team)
    puzzle = models.ForeignKey(Puzzle)
    start_time = models.DateTimeField(default=datetime.now)
    solved = models.BooleanField(default=False)

    def __str__(self):
        s = 'can see'
        if self.solved:
            s = 'has solved'
        return '%s %s %s' % (str(self.team), s, str(self.puzzle))

    class Meta:
        unique_together = ('team', 'puzzle')
        verbose_name_plural = 'Puzzle access'

# ----------------------- 2014-specific stuff ---------------------

class Y2014MitMapNode(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.IntegerField()

    def __str__(self):
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
