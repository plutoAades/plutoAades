from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import PrivateMessage  # 确保使用 PrivateMessage
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Q
from .models import Message
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

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

@login_required
def messages_history(request, username):
    other = get_object_or_404(User, username=username)
    qs = PrivateMessage.objects.filter(
        (Q(sender=request.user) & Q(receiver=other)) |
        (Q(sender=other) & Q(receiver=request.user))
    ).order_by('timestamp')[:200]
    data = [{
        'id': m.id,
        'user': m.sender.username if m.sender else '',
        'message_type': m.message_type if hasattr(m, 'message_type') else 'text',
        'content': m.content,
        'file_url': m.file.url if getattr(m, 'file', None) else '',
        'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
    } for m in qs]
    return JsonResponse({'messages': data})

@csrf_exempt
@require_POST
@login_required
def send_ajax_message(request):
    try:
        receiver_id = int(request.POST.get('receiver_id') or 0)
    except Exception:
        return JsonResponse({'error': 'invalid receiver_id'}, status=400)
    content = (request.POST.get('content') or '').strip()
    if not content:
        return JsonResponse({'error': 'empty content'}, status=400)
    receiver = get_object_or_404(User, id=receiver_id)
    msg = PrivateMessage.objects.create(sender=request.user, receiver=receiver, content=content, message_type='text')
    return JsonResponse({
        'ok': True,
        'id': msg.id,
        'user': request.user.username,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
    })