from django.contrib import admin

from core.models import Game, GamePlayers


class GamePlayersInline(admin.TabularInline):
    model = GamePlayers
    extra = 0


class GameAdmin(admin.ModelAdmin):
    readonly_fields = ('current_turn',)
    inlines = [GamePlayersInline]


admin.site.register(Game, GameAdmin)
