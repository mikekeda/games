from django.core.asgi import get_asgi_application
from django.conf.urls import url

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from core.consumers import WsGame


games = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    url(r"^ws/game/(?P<game_id>\w+)$", WsGame.as_asgi()),
                ]
            )
        ),
    }
)
