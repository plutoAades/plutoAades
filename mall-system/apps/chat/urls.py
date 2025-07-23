from django.urls import path
from . import views

urlpatterns = [
    path('private/<int:user_id>/', views.private_chat, name='private_chat'),
    path('send/', views.send_private_message, name='send_private_message'),
    path('delete/<int:message_id>/', views.delete_private_message, name='delete_private_message'),
]