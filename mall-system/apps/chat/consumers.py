import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import Message, ChatGroup
from asgiref.sync import sync_to_async

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_type = self.scope['url_route']['kwargs'].get('room_type', 'group')
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_type}_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('message_type', 'text')
        content = data.get('content', '')
        file_url = data.get('file_url', '')
        action = data.get('action', 'send')
        user = self.scope['user']

        # 发送消息
        if action == 'send':
            message = await sync_to_async(Message.objects.create)(
                sender=user,
                group=await sync_to_async(ChatGroup.objects.get)(name=self.room_name) if self.room_type == 'group' else None,
                receiver=await sync_to_async(User.objects.get)(username=self.room_name) if self.room_type == 'private' else None,
                content=content,
                message_type=msg_type,
                file=file_url if msg_type in ['image', 'file'] else None
            )
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': content,
                    'user': user.username,
                    'message_type': msg_type,
                    'file_url': file_url,
                    'id': message.id,
                    'timestamp': str(message.timestamp),
                }
            )
        # 撤回消息
        elif action == 'revoke':
            msg_id = data.get('id')
            await sync_to_async(Message.objects.filter(id=msg_id).update)(is_revoked=True)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'revoke_message',
                    'id': msg_id,
                }
            )
        # 删除消息
        elif action == 'delete':
            ids = data.get('ids', [])
            await sync_to_async(Message.objects.filter(id__in=ids).update)(is_deleted=True)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'delete_message',
                    'ids': ids,
                }
            )
        # 转发消息
        elif action == 'forward':
            msg_id = data.get('id')
            orig_msg = await sync_to_async(Message.objects.get)(id=msg_id)
            new_msg = await sync_to_async(Message.objects.create)(
                sender=user,
                group=orig_msg.group,
                receiver=orig_msg.receiver,
                content=orig_msg.content,
                message_type=orig_msg.message_type,
                file=orig_msg.file,
                forwarded_from=orig_msg
            )
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': new_msg.content,
                    'user': user.username,
                    'message_type': new_msg.message_type,
                    'file_url': new_msg.file.url if new_msg.file else '',
                    'id': new_msg.id,
                    'timestamp': str(new_msg.timestamp),
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def revoke_message(self, event):
        await self.send(text_data=json.dumps({'action': 'revoke', 'id': event['id']}))

    async def delete_message(self, event):
        await self.send(text_data=json.dumps({'action': 'delete', 'ids': event['ids']}))