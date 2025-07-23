from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import PrivateMessage
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def private_chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    messages = PrivateMessage.objects.filter(
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user]
    ).order_by('timestamp')  # 按时间排序
    return render(request, 'chat/private_chat.html', {
        'other_user': other_user,
        'messages': messages,
    })

@login_required
def send_private_message(request):
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content')
        receiver = get_object_or_404(User, id=receiver_id)
        if content.strip():
            PrivateMessage.objects.create(sender=request.user, receiver=receiver, content=content)
        return redirect('private_chat', user_id=receiver_id)

@login_required
def delete_private_message(request, message_id):
    message = get_object_or_404(PrivateMessage, id=message_id)
    if message.sender == request.user or message.receiver == request.user:
        message.delete()
    return redirect('private_chat', user_id=message.receiver.id if message.sender == request.user else message.sender.id)