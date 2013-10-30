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
        ordering = ['order']
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
