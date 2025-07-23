from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrivateMessageViewSet

router = DefaultRouter()
router.register(r'private-messages', PrivateMessageViewSet)

urlpatterns = [
    path('', include(router.urls)),  # API 路由
]