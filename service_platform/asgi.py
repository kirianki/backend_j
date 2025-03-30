import os
import django  # Ensure Django initializes before anything else
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Ensure Django settings are loaded
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service_platform.settings")
django.setup()  # **Fix: Initialize Django before imports**

import communications.routing  # Import after django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Handle HTTP requests
    "websocket": AuthMiddlewareStack(
        URLRouter(communications.routing.websocket_urlpatterns)
    ),
})
