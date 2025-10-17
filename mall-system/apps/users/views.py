from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
import json
from apps.products.views import get_cart_items
from apps.products.models import Product
from apps.chat.models import Message

User = get_user_model()

# 优先使用 apps.users.forms 中的 LoginForm；若没有则使用 Django 的 AuthenticationForm 作为兼容替代
try:
    from .forms import LoginForm
except Exception:
    from django.contrib.auth.forms import AuthenticationForm as LoginForm

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
            return redirect('dashboard')  # 登录成功后跳转到商品列表
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})
def logout_view(request):
    logout(request)  # 清除会话信息
    return redirect('login')  # 跳转到登录页面
@login_required
def user_profile(request):
    return render(request, 'users/profile.html', {'user': request.user})
@login_required
def dashboard_view(request):
    q = request.GET.get('q', '').strip()
    qs = Product.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    qs = qs.order_by('-id')
    paginator = Paginator(qs, 5)
    page_obj = paginator.get_page(request.GET.get('page'))

    cart_items, cart_total_count, cart_total_price = get_cart_items(request)

    # 管理员目标（取第一个 superuser）
    admin = User.objects.filter(is_superuser=True).first()
    admin_username = admin.username if admin else ''
    admin_id = admin.id if admin else None

    # 管理员侧边栏显示与其有对话的用户
    chat_users = []
    if request.user.is_superuser:
        user_ids = Message.objects.exclude(sender=None).values_list('sender__id', flat=True).distinct()
        chat_users = User.objects.filter(id__in=user_ids)

    context = {
        'products': page_obj,
        'cart_items': cart_items,
        'cart_total_count': cart_total_count,
        'cart_total_price': cart_total_price,
        'q': q,
        'admin_username': admin_username,
        'admin_id': admin_id,            # 新增：管理员 id
        'chat_users': chat_users,
    }
    return render(request, 'users/dashboard.html', context)
@login_required
def category_view(request, category):
    q = request.GET.get('q', '').strip()
    # 支持“未分类”特殊处理，并根据 q 进行 name 模糊匹配
    if category == '未分类':
        qs = Product.objects.filter(Q(category__isnull=True) | Q(category='未分类'))
    else:
        qs = Product.objects.filter(category=category)

    if q:
        qs = qs.filter(name__icontains=q)

    qs = qs.order_by('-id')
    paginator = Paginator(qs, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    cart_items, cart_total_count, cart_total_price = get_cart_items(request)
    context = {
        'products': page_obj,
        'cart_items': cart_items,
        'cart_total_count': cart_total_count,
        'cart_total_price': cart_total_price,
        'category': category,
        'q': q,  # 将搜索词传回模板以便回显和分页保留
    }
    return render(request, 'users/category.html', context)
@login_required
def dashboard_stats(request):
    # 仅管理员可见
    if not request.user.is_superuser:
        return redirect('dashboard')

    # 饼图按 Product.type（若不存在则回退到 category）
    field_for_pie = 'type'
    try:
        Product._meta.get_field('type')
    except Exception:
        field_for_pie = 'category'

    pie_qs = Product.objects.values(field_for_pie).annotate(count=Count(field_for_pie)).order_by('-count')
    pie_labels = [(item[field_for_pie] if item[field_for_pie] else '未设置') for item in pie_qs]
    pie_data = [item['count'] for item in pie_qs]

    # 条形图按 category 统计每类数量
    bar_qs = Product.objects.values('category').annotate(count=Count('category')).order_by('-count')
    bar_labels = [(item['category'] if item['category'] else '未分类') for item in bar_qs]
    bar_data = [item['count'] for item in bar_qs]

    context = {
        'pie_labels': json.dumps(pie_labels, ensure_ascii=False),
        'pie_data': json.dumps(pie_data),
        'pie_field': field_for_pie,
        'bar_labels': json.dumps(bar_labels, ensure_ascii=False),
        'bar_data': json.dumps(bar_data),
    }
    return render(request, 'users/stats.html', context)