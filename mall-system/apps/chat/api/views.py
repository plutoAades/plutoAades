from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import PrivateMessage, Message, ChatGroup
from .serializers import PrivateMessageSerializer, MessageSerializer, ChatGroupSerializer

class PrivateMessageViewSet(viewsets.ModelViewSet):
    queryset = PrivateMessage.objects.all()
    serializer_class = PrivateMessageSerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        message = self.get_object()
        message.is_revoked = True
        message.save()
        return Response({'status': '消息已撤回'})

    @action(detail=True, methods=['post'])
    def forward(self, request, pk=None):
        message = self.get_object()
        new_message = Message.objects.create(
            sender=request.user,
            receiver=message.receiver,
            group=message.group,
            content=message.content,
            file=message.file,
            message_type=message.message_type,
            forwarded_from=message
        )
        return Response(MessageSerializer(new_message).data)

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        ids = request.data.get('ids', [])
        Message.objects.filter(id__in=ids).update(is_deleted=True)
        return Response({'status': '批量删除成功'})

class ChatGroupViewSet(viewsets.ModelViewSet):
    queryset = ChatGroup.objects.all()
    serializer_class = ChatGroupSerializer