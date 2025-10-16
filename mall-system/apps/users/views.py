from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import RegisterForm, LoginForm
from apps.products.views import get_cart_items
from apps.products.models import Product
from django.core.paginator import Paginator
from django.db.models import Q

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
    # 支持搜索 q 参数（基于 product.name 模糊匹配），并分页（每页10条）
    q = request.GET.get('q', '').strip()
    products_qs = Product.objects.all()
    if q:
        products_qs = products_qs.filter(name__icontains=q)
    products_qs = products_qs.order_by('-id')

    paginator = Paginator(products_qs, 5)  # 每页10条
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    cart_items, cart_total_count, cart_total_price = get_cart_items(request)
    context = {
        'products': page_obj,
        'cart_items': cart_items,
        'cart_total_count': cart_total_count,
        'cart_total_price': cart_total_price,
        'q': q,  # 将搜索词传到模板，便于表单回显与分页链接保留
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