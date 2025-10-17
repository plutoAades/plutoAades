from django.urls import path
from . import views

urlpatterns = [
    path('history/<str:username>/', views.messages_history, name='chat_messages_history'),
    path('send_ajax/', views.send_ajax_message, name='chat_send_ajax'),
    # 可选：其它 chat 路由...
]