from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from django.contrib.auth import get_user_model

from .models import PrivateMessage  # 使用私聊模型

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 路由 path: /ws/chat/<room_type>/<room_name>/
        self.room_type = self.scope['url_route']['kwargs'].get('room_type')
        self.room_name = self.scope['url_route']['kwargs'].get('room_name')
        self.group_name = f'chat_{self.room_type}_{self.room_name}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f'[chat] connect user={self.scope.get("user")} group={self.group_name}')

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f'[chat] disconnect group={self.group_name} code={close_code}')

    async def receive(self, text_data=None, bytes_data=None):
        print('[chat] receive raw:', text_data)
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except Exception as e:
            print('[chat] JSON parse error', e)
            return
        if data.get('action') != 'send':
            return
        content = (data.get('content') or '').strip()
        if not content:
            return

        sender = self.scope.get('user') if self.scope.get('user').is_authenticated else None
        receiver = None

        # 私聊房间名约定：username1__username2（按字母排序）
        if self.room_type == 'private':
            parts = self.room_name.split('__')
            other = None
            if sender and sender.username in parts:
                other = parts[1] if parts[0] == sender.username else parts[0]
            else:
                other = self.room_name
            if other:
                receiver = await database_sync_to_async(lambda: User.objects.filter(username=other).first())()

        msg = None
        if sender and receiver:
            try:
                msg = await database_sync_to_async(self._create_private_message)(sender, receiver, content)
                print('[chat] saved private message id=', getattr(msg, 'id', None))
            except Exception as e:
                print('[chat] save private message error', e)

        payload = {
            'user': sender.username if sender else '匿名',
            'message': content,
            'timestamp': getattr(msg, 'timestamp', None) and msg.timestamp.strftime('%Y-%m-%d %H:%M:%S') or '',
        }

        # 广播字符串 JSON（前端直接 JSON.parse）
        await self.channel_layer.group_send(self.group_name, {
            'type': 'chat.message',
            'text': json.dumps(payload),
        })

    async def chat_message(self, event):
        # event['text'] 是字符串 JSON
        await self.send(text_data=event['text'])

    def _create_private_message(self, sender, receiver, content):
        return PrivateMessage.objects.create(sender=sender, receiver=receiver, content=content)