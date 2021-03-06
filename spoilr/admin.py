from django.contrib import admin
from .models import *

class MetapuzzleAdmin(admin.ModelAdmin):
    def teams_solved(metapuzzle):
        return MetapuzzleSolve.objects.filter(metapuzzle=metapuzzle).count()
    teams_solved.short_description = 'Teams Solved'
    list_display = ('__str__', teams_solved)
    search_fields = ['url', 'name']
    ordering = ['order']

class InteractionAdmin(admin.ModelAdmin):
    def teams_pending(puzzle):
        return InteractionAccess.objects.filter(interaction=interaction, accomplished=False).count()
    teams_pending.short_description = 'Teams Pending'
    def teams_accomplished(interaction):
        return InteractionAccess.objects.filter(interaction=interaction, accomplished=True).count()
    teams_accomplished.short_description = 'Teams Accomplished'
    list_display = ('__str__', teams_pending, teams_accomplished)
    search_fields = ['url', 'name']
    ordering = ['order']

class RoundPuzzleInline(admin.TabularInline):
    model = Puzzle
    extra = 0
    ordering = ['order']

class RoundAdmin(admin.ModelAdmin):
    def teams_open(round):
        return RoundAccess.objects.filter(round=round).count()
    teams_open.short_description = 'Teams Open'
    def puzzles(round):
        return Puzzle.objects.filter(round=round).count()
    puzzles.short_description = 'Puzzles'
    list_display = ('__str__', puzzles, teams_open)
    search_fields = ['url', 'name']
    inlines = [RoundPuzzleInline]
    ordering = ['order']

class PuzzleAdmin(admin.ModelAdmin):
    def teams_open(puzzle):
        return PuzzleAccess.objects.filter(puzzle=puzzle).count()
    teams_open.short_description = 'Teams Open'
    def teams_solved(puzzle):
        return PuzzleAccess.objects.filter(puzzle=puzzle,solved=True).count()
    teams_solved.short_description = 'Teams Solved'
    list_display = ('__str__', 'name', 'round', teams_open, teams_solved)
    list_filter = ('round__name',)
    search_fields = ['url', 'name']
    ordering = ['order']

admin.site.register(Interaction, InteractionAdmin)
admin.site.register(Metapuzzle, MetapuzzleAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Puzzle, PuzzleAdmin)

class TeamPhoneAdmin(admin.ModelAdmin):
    def team_name(data):
        return data.team.name
    list_display = (team_name, 'phone')
    search_fields = [team_name, 'phone']

admin.site.register(TeamPhone, TeamPhoneAdmin)

class TeamRoundInline(admin.TabularInline):
    model = Team.rounds.through
    extra = 0
    ordering = ['round__order']

class TeamPuzzleInline(admin.TabularInline):
    model = Team.puzzles.through
    extra = 0
    ordering = ['puzzle__round__order', 'puzzle__order']

class TeamPhoneInline(admin.TabularInline):
    model = TeamPhone
    extra = 0

class TeamAdmin(admin.ModelAdmin):
    def rounds_open(team):
        return team.rounds.count()
    rounds_open.short_description = 'Rounds Open'
    def metapuzzles_solved(team):
        return MetapuzzleSolve.objects.filter(team=team).count()
    metapuzzles_solved.short_description = 'Metapuzzles Solved'
    def puzzles_open(team):
        return team.puzzles.count()
    puzzles_open.short_description = 'Puzzles Open'
    def puzzles_solved(team):
        return team.puzzles.filter(puzzleaccess__solved=True).count()
    puzzles_solved.short_description = 'Puzzles Solved'
    def puzzles_unsolved(team):
        return team.puzzles.filter(puzzleaccess__solved=False).count()
    puzzles_unsolved.short_description = 'Puzzles Unsolved'
    inlines = [TeamRoundInline, TeamPuzzleInline, TeamPhoneInline]
    list_display = ('__str__', 'username', rounds_open, metapuzzles_solved, puzzles_open, puzzles_solved, puzzles_unsolved)
    search_fields = ['name', 'username']

admin.site.register(Team, TeamAdmin)

class LogTeamFilter(admin.SimpleListFilter):
    title = 'team'
    parameter_name = 'team'
    def lookups(self, request, model_admin):
        return [(x.name, x.name) for x in Team.objects.all()]
    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(team__name=self.value())

class SystemLogAdmin(admin.ModelAdmin):
    def team_name(data):
        if data.team:
            return data.team.name
        else:
            return ''
    list_display = ('timestamp', 'event_type', team_name, 'object_id', 'message')
    list_filter = ('event_type', LogTeamFilter, 'object_id')
    search_fields = [team_name, 'event_type', 'object_id', 'message']

admin.site.register(SystemLog, SystemLogAdmin)

class TeamLogAdmin(admin.ModelAdmin):
    def team_name(data):
        return data.team.name
    list_display = ('timestamp', team_name, 'event_type', 'object_id', 'message')
    list_filter = (LogTeamFilter, 'event_type', 'object_id')
    search_fields = [team_name, 'event_type', 'object_id', 'message']

admin.site.register(TeamLog, TeamLogAdmin)

class MetapuzzleSolveMetapuzzleFilter(admin.SimpleListFilter):
    title = 'metapuzzle'
    parameter_name = 'metapuzzle'
    def lookups(self, request, model_admin):
        return [(x.name, x.name) for x in Metapuzzle.objects.all()]
    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(metapuzzle__name=self.value())

class MetapuzzleSolveAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'team', 'metapuzzle')
    list_filter = ('team__name', MetapuzzleSolveMetapuzzleFilter)
    search_fields = ['team__name', 'metapuzzle__name']
    ordering = ['team__name', 'metapuzzle__order']

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
    list_display = ('__str__', 'team', 'round')
    list_filter = ('team__name', RoundAccessRoundFilter)
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
    list_display = ('__str__', 'team', 'puzzle', 'solved')
    list_filter = ('team__name', PuzzleAccessRoundFilter, 'solved')
    search_fields = ['team__name', 'puzzle__name', 'puzzle__round__name']
    ordering = ['team__name', 'puzzle__round__order', 'puzzle__order']

class InteractionAccessAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'team', 'interaction', 'accomplished')
    list_filter = ('team__name', 'interaction', 'accomplished')
    search_fields = ['team__name', 'interaction__name']
    ordering = ['team__name', 'interaction__order']

admin.site.register(MetapuzzleSolve,MetapuzzleSolveAdmin)
admin.site.register(RoundAccess,RoundAccessAdmin)
admin.site.register(PuzzleAccess,PuzzleAccessAdmin)
admin.site.register(InteractionAccess,InteractionAccessAdmin)

class PuzzleSubmissionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'timestamp', 'team', 'puzzle', 'phone', 'resolved')
    list_filter = ('team__name', PuzzleAccessRoundFilter, 'resolved')
    search_fields = ['team__name', 'puzzle__name', 'puzzle__round__name']
    ordering = ['timestamp']

admin.site.register(PuzzleSubmission,PuzzleSubmissionAdmin)

class MetapuzzleSubmissionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'timestamp', 'team', 'metapuzzle', 'phone', 'resolved')
    list_filter = ('team__name', 'metapuzzle__name', 'resolved')
    search_fields = ['team__name', 'metapuzzle__name']
    ordering = ['timestamp']

admin.site.register(MetapuzzleSubmission,MetapuzzleSubmissionAdmin)

class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'timestamp', 'team', 'phone', 'comment', 'resolved')
    list_filter = ('team__name', 'resolved')
    search_fields = ['team__name', 'comment']
    ordering = ['timestamp']

admin.site.register(ContactRequest,ContactRequestAdmin)

class QueueHandlerAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email')
    list_filter = ('name', 'team__name')
    search_fields = ['name', 'email', 'team__name']

admin.site.register(QueueHandler,QueueHandlerAdmin)

class PuzzleSurveyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'fun', 'difficulty', 'timestamp')
    list_filter = ('team__name', PuzzleAccessRoundFilter, 'fun', 'difficulty')
    search_fields = ['team__name', 'puzzle__name', 'puzzle__round__name', 'comment']

admin.site.register(PuzzleSurvey,PuzzleSurveyAdmin)

# ----------------------- 2014-specific stuff ---------------------

class Y2014TeamDataAdmin(admin.ModelAdmin):
    list_display = ('team', 'points', 'humpty_pieces')
    search_fields = ['team__name']

admin.site.register(Y2014TeamData, Y2014TeamDataAdmin)

class Y2014MitPuzzleDataAdmin(admin.ModelAdmin):
    def mit_meta(data):
        return data.mit_meta()
    mit_meta.short_description = 'MIT Meta'
    def puzzle_name(data):
        return data.puzzle.name
    puzzle_name.short_description = 'Puzzle Name'
    list_display = ('card', mit_meta, puzzle_name)
    search_fields = ['card', 'puzzle__name']
    ordering = ['card']

admin.site.register(Y2014MitPuzzleData, Y2014MitPuzzleDataAdmin)

class Y2014MitCardAdmin(admin.ModelAdmin):
    def mit_meta(data):
        return data.mit_meta()
    list_display = ('name', mit_meta, 'start')
    search_fields = ['name']
    ordering = ['order']

admin.site.register(Y2014MitCard, Y2014MitCardAdmin)

class Y2014MitMapEdgeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'card1', 'card2')
    search_fields = ['card1', 'card2']
    ordering = ['card1__order', 'card2__order']

admin.site.register(Y2014MitMapEdge, Y2014MitMapEdgeAdmin)

class Y2014MitMetapuzzleSubmissionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'timestamp', 'team', 'phone', 'resolved')
    list_filter = ('team__name', 'resolved')
    search_fields = ['team__name']
    ordering = ['timestamp']

admin.site.register(Y2014MitMetapuzzleSubmission,Y2014MitMetapuzzleSubmissionAdmin)

class Y2014CaucusAnswerDataAdmin(admin.ModelAdmin):
    list_display = ('bird',)

admin.site.register(Y2014CaucusAnswerData, Y2014CaucusAnswerDataAdmin)

class Y2014KnightsAnswerDataAdmin(admin.ModelAdmin):
    list_display = ('piece', 'color', 'order')
    list_filter = ('piece', 'color')

admin.site.register(Y2014KnightsAnswerData, Y2014KnightsAnswerDataAdmin)

class Y2014PartyAnswerDataAdmin(admin.ModelAdmin):
    list_display = ('type1', 'type2', 'level')
    list_filter = ('type1', 'type2', 'level')

admin.site.register(Y2014PartyAnswerData, Y2014PartyAnswerDataAdmin)

class Y2014PwaGarciaparraUrlSubmissionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'timestamp', 'team', 'phone', 'resolved')
    list_filter = ('team__name', 'resolved')
    search_fields = ['team__name']
    ordering = ['timestamp']

admin.site.register(Y2014PwaGarciaparraUrlSubmission, Y2014PwaGarciaparraUrlSubmissionAdmin)

