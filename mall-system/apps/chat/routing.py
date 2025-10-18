from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # 与前端一致的路径：/ws/chat/<room_type>/<room_name>/
    re_path(r'ws/chat/(?P<room_type>[^/]+)/(?P<room_name>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
]