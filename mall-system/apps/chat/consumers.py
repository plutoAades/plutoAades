# chat/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 调试：记录 scope 中关键信息
        try:
            user = self.scope.get('user')
            logger.info("WS connect attempt. user=%s, auth=%s, headers=%s",
                        getattr(user, 'username', None),
                        bool(user and user.is_authenticated),
                        dict(self.scope.get('headers', [])))
        except Exception as e:
            logger.exception("connect debug error: %s", e)

        # 如果未认证，可视情况拒绝或允许（这里示例允许连接但不会授权特殊操作）
        if self.scope.get('user') is None or not getattr(self.scope['user'], 'is_authenticated', False):
            # 如果你想强制登录才能连，使用下面一行改为拒绝并记录原因
            # await self.close(code=4003); return
            logger.warning("Anonymous WS connection (session not sent).")
        # 继续常规组加入/accept
        self.room_name = self.scope['url_route']['kwargs'].get('room_name')
        self.room_group_name = f'chat_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')

        if action == 'send':
            content = text_data_json.get('content', '')
            user = getattr(self.scope.get('user'), 'username', '匿名')
            timestamp = self.get_current_timestamp()

            # 广播消息到当前房间组
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'user': user,
                    'message': content,
                    'timestamp': timestamp,
                }
            )

            # 通知所有管理员：使用 admins 组
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
        # 使用 group_send 广播到 admins 组（管理员连接时会加入该组）
        await self.channel_layer.group_send(
            'admins',
            {
                'type': 'admin_notification',
                'message': f"New message from {user}: {message}",
            }
        )

    async def admin_notification(self, event):
        # 转发给当前 websocket 客户端（管理员）
        await self.send(text_data=json.dumps({
            'system': True,
            'message': event.get('message', '')
        }))

    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

