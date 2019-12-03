from django.conf.urls import url

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from core.consumers import WsGame


games = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            url(r"^ws/game/(?P<game_id>\w+)$", WsGame),
        ])
    ),
})
