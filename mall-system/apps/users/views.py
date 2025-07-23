from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import RegisterForm, LoginForm

def user_list(request):
    users = User.objects.all()
    return JsonResponse({'users': list(users.values())})

def user_detail(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({'user': {'id': user.id, 'username': user.username, 'email': user.email}})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # 登录用户
            return redirect('product_list')  # 登录成功后跳转到商品列表
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)  # 清除会话信息
    return redirect('login')  # 跳转到登录页面

@login_required
def user_profile(request):
    return render(request, 'users/profile.html', {'user': request.user})