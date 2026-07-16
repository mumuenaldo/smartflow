# smartflow_project/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import registry.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartflow_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            registry.routing.websocket_urlpatterns
        )
    ),
})