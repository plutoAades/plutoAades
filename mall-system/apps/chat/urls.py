from django.urls import path
from . import views

urlpatterns = [
    # path('history/<str:username>/', views.messages_history, name='chat_messages_history'),
    # path('send_ajax/', views.send_ajax_message, name='chat_send_ajax'),
    path('h5/', views.h5_chat, name='h5_chat'),  # 新增：H5 聊天页面
    # 可选：其它 chat 路由...
]