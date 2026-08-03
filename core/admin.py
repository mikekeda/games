from django.contrib import admin

from core.models import Game, GameMove, GamePlayers


class GamePlayersInline(admin.TabularInline):
    model = GamePlayers
    extra = 0


class GameMoveInline(admin.TabularInline):
    model = GameMove
    extra = 0
    fields = ("number", "player", "move", "created")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


class GameAdmin(admin.ModelAdmin):
    list_display = ("pk", "game", "current_turn", "winner", "completed", "modified")
    list_filter = ("game", "completed")
    readonly_fields = ("current_turn", "winner", "completed", "created", "modified")
    inlines = [GamePlayersInline, GameMoveInline]


admin.site.register(Game, GameAdmin)
