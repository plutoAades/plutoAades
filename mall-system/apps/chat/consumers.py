# chat/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # 加入房间
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json['action']

        if action == 'send':
            content = text_data_json['content']
            user = self.scope['user'].username
            timestamp = self.get_current_timestamp()

            # 广播消息到房间内所有用户（包括管理员）
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'user': user,
                    'message': content,
                    'timestamp': timestamp,
                }
            )

            # 发送提醒给所有管理员
            await self.send_admin_notification(user, content)

    async def chat_message(self, event):
        user = event['user']
        message = event['message']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'user': user,
            'message': message,
            'timestamp': timestamp,
        }))

    async def send_admin_notification(self, user, message):
        # 获取所有管理员
        admins = User.objects.filter(is_superuser=True)

        # 广播提醒到所有管理员的 WebSocket 连接
        for admin in admins:
            await self.channel_layer.send(
                admin.username,  # 使用管理员的用户名作为键名，确保是管理员的连接
                {
                    'type': 'admin_notification',
                    'message': f"New message from {user}: {message}",
                }
            )

    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

