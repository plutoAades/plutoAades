from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
import json
from apps.products.models import Product, ProductReview
from apps.chat.models import Message

User = get_user_model()

# 优先使用 apps.users.forms 中的 LoginForm；若没有则使用 Django 的 AuthenticationForm 作为兼容替代
try:
    from .forms import LoginForm
except Exception:
    from django.contrib.auth.forms import AuthenticationForm as LoginForm

# 新增：RegisterForm 兼容导入（若没有自定义表单则使用 UserCreationForm）
try:
    from .forms import RegisterForm
except Exception:
    from django.contrib.auth.forms import UserCreationForm as RegisterForm

try:
    from apps.products.views import get_cart_items
except Exception:
    from decimal import Decimal
    from apps.products.models import Product

    def get_cart_items(request):
        """
        兼容回退实现：从 session['cart'] 读取购物车并计算 line_total / total_price
        返回 (items, total_count, total_price)
        items 每项为 dict: {'product': Product, 'quantity': int, 'line_total': Decimal}
        """
        cart = request.session.get('cart', {}) or {}
        items = []
        total_count = 0
        total_price = Decimal('0.00')
        for pid, qty in list(cart.items()):
            try:
                product = Product.objects.get(pk=pid)
            except Product.DoesNotExist:
                cart.pop(pid, None)
                continue
            try:
                q = int(qty)
            except Exception:
                q = 0
            if q <= 0:
                cart.pop(pid, None)
                continue
            price = getattr(product, 'price', Decimal('0.00')) or Decimal('0.00')
            line_total = price * q
            items.append({'product': product, 'quantity': q, 'line_total': line_total})
            total_count += q
            total_price += line_total
        request.session['cart'] = cart
        return items, total_count, total_price

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
            return redirect('dashboard')
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
    # ...existing code that构建 context ...
    # 假定已有 context 变量存在，示例为保留原有 context 后追加推荐
    context = {}  # ...existing context assignment...
    # 推荐逻辑：优先取用户评分 >=4 的商品，按最新评价排序，最多 2 个；不足时补最近商品
    recommended = []
    if request.user.is_authenticated:
        prod_ids = (ProductReview.objects
                    .filter(user=request.user, rating__gte=4)
                    .order_by('-created_at')
                    .values_list('product_id', flat=True)
                    .distinct())
        if prod_ids:
            qs = Product.objects.filter(id__in=prod_ids).distinct()[:2]
            recommended = list(qs)
        if len(recommended) < 2:
            extra_qs = Product.objects.exclude(id__in=[p.id for p in recommended]).order_by('-id')[:(2 - len(recommended))]
            recommended += list(extra_qs)
    context['recommended_products'] = recommended

    return render(request, 'users/profile.html', context)
@login_required
def dashboard_view(request):
    """
    优化：分页并限制查询字段，避免登录后一次性加载大量 Product 导致变慢。
    """
    q = request.GET.get('q', '').strip()
    qs = Product.objects.all().order_by('-id')

    if q:
        qs = qs.filter(name__icontains=q)

    # 只加载模板常用字段，减少数据库/ORM 开销（根据实际字段调整）
    qs = qs.only('id', 'name', 'price', 'stock', 'image_main')

    # 分页：每页 10 条（可调整）
    paginator = Paginator(qs, 5)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    cart_items, cart_total_count, cart_total_price = get_cart_items(request)

    # 获取对话用户列表
    chat_users = User.objects.filter(is_active=True)

    context = {
        'products': products_page,
        'q': q,
        'cart_items': cart_items,
        'cart_total_count': cart_total_count,
        'cart_total_price': cart_total_price,
        'admin_username': 'admin',
        'chat_users': chat_users,  # 添加对话用户列表
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