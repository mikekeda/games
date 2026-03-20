from django.core.asgi import get_asgi_application
from django.urls import re_path

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from core.consumers import WsGame

games = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    re_path(r"^ws/game/(?P<game_id>\w+)$", WsGame.as_asgi()),
                ]
            )
        ),
    }
)
