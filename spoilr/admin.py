from django.contrib import admin
from .models import *

class RoundPuzzleInline(admin.TabularInline):
    model = Puzzle
    extra = 0
    ordering = ['order']

class RoundAdmin(admin.ModelAdmin):
    def teams_open(round):
        return len(RoundAccess.objects.filter(round=round))
    teams_open.short_description = 'Teams Open'
    def teams_solved(round):
        return len(RoundAccess.objects.filter(round=round,solved=True))
    def puzzles(round):
        return len(Puzzle.objects.filter(round=round))
    puzzles.short_description = 'Puzzles'
    list_display = ('__str__', puzzles, teams_open, teams_solved)
    search_fields = ['url', 'name']
    inlines = [RoundPuzzleInline]
    ordering = ['order']

class PuzzleAdmin(admin.ModelAdmin):
    def teams_open(puzzle):
        return len(PuzzleAccess.objects.filter(puzzle=puzzle))
    teams_open.short_description = 'Teams Open'
    def teams_solved(puzzle):
        return len(PuzzleAccess.objects.filter(puzzle=puzzle,solved=True))
    teams_solved.short_description = 'Teams Solved'
    list_display = ('__str__', 'name', 'round', teams_open, teams_solved)
    list_filter = ('round__name',)
    search_fields = ['url', 'name']
    ordering = ['order']

admin.site.register(Round, RoundAdmin)
admin.site.register(Puzzle, PuzzleAdmin)

class TeamRoundInline(admin.TabularInline):
    model = Team.rounds.through
    exclude = ('start_time',)
    extra = 0
    ordering = ['round__order']

class TeamPuzzleInline(admin.TabularInline):
    model = Team.puzzles.through
    exclude = ('start_time',)
    extra = 0
    ordering = ['puzzle__round__order', 'puzzle__order']

class TeamAdmin(admin.ModelAdmin):
    def rounds_open(team):
        return len(team.rounds.all())
    rounds_open.short_description = 'Rounds Open'
    def rounds_solved(team):
        return len(team.rounds.filter(roundaccess__solved=True))
    rounds_solved.short_description = 'Rounds Solved'
    def puzzles_open(team):
        return len(team.puzzles.all())
    puzzles_open.short_description = 'Puzzles Open'
    def puzzles_solved(team):
        return len(team.puzzles.filter(puzzleaccess__solved=True))
    puzzles_solved.short_description = 'Puzzles Solved'
    def puzzles_unsolved(team):
        return len(team.puzzles.filter(puzzleaccess__solved=False))
    puzzles_unsolved.short_description = 'Puzzles Unsolved'
    inlines = [TeamRoundInline, TeamPuzzleInline]
    list_display = ('__str__', 'username', rounds_open, rounds_solved, puzzles_open, puzzles_solved, puzzles_unsolved)
    search_fields = ['name', 'username']

admin.site.register(Team, TeamAdmin)

class RoundAccessRoundFilter(admin.SimpleListFilter):
    title = 'round'
    parameter_name = 'round'
    def lookups(self, request, model_admin):
        return [(x.name, x.name) for x in Round.objects.all()]
    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(round__name=self.value())

class RoundAccessAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'team', 'round', 'start_time', 'solved')
    list_filter = ('team__name', RoundAccessRoundFilter, 'solved')
    search_fields = ['team__name', 'round__name']
    ordering = ['team__name', 'round__order']
    
class PuzzleAccessRoundFilter(admin.SimpleListFilter):
    title = 'round'
    parameter_name = 'round'
    def lookups(self, request, model_admin):
        return [(x.name, x.name) for x in Round.objects.all()]
    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(puzzle__round__name=self.value())

class PuzzleAccessAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'team', 'puzzle', 'start_time', 'solved')
    list_filter = ('team__name', PuzzleAccessRoundFilter, 'solved')
    search_fields = ['team__name', 'puzzle__name', 'puzzle__round__name']
    ordering = ['team__name', 'puzzle__round__order', 'puzzle__order']

admin.site.register(RoundAccess,RoundAccessAdmin)
admin.site.register(PuzzleAccess,PuzzleAccessAdmin)
