from rest_framework import viewsets
from django.contrib.auth import get_user_model
User = get_user_model()
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer