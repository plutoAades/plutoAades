from rest_framework import viewsets
from ..models import PrivateMessage
from .serializers import PrivateMessageSerializer

class PrivateMessageViewSet(viewsets.ModelViewSet):
    queryset = PrivateMessage.objects.all()
    serializer_class = PrivateMessageSerializer