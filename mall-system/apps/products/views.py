from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import ListView, DetailView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Prefetch
from .models import Product, ProductImage
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from decimal import Decimal


# =======================
# 辅助函数：获取购物车信息
# =======================
def get_cart_items(request):
    """
    返回 (cart_items, total_count, total_price)
    cart 存在于 session，格式: { "<product_id>": <quantity>, ... }
    cart_items 列表中每项为 dict: {'product': Product, 'quantity': int, 'line_total': Decimal}
    """
    cart = request.session.get('cart', {}) or {}
    items = []
    total_count = 0
    total_price = Decimal('0.00')
    for pid, qty in list(cart.items()):
        try:
            product = Product.objects.get(pk=pid)
        except Product.DoesNotExist:
            # 清理已不存在的商品
            cart.pop(pid, None)
            continue
        try:
            qty_i = int(qty)
        except Exception:
            qty_i = 0
        if qty_i <= 0:
            cart.pop(pid, None)
            continue
        line_total = (product.price or Decimal('0.00')) * qty_i
        items.append({'product': product, 'quantity': qty_i, 'line_total': line_total})
        total_count += qty_i
        total_price += line_total
    # 把可能的清理回写 session
    request.session['cart'] = cart
    return items, total_count, total_price


# =======================
# 商品列表视图（分页 + 缓存 + 优化）
# =======================
@method_decorator(cache_page(60 * 5), name='dispatch')  # 缓存5分钟
class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 10  # 每页10条数据

    def get_queryset(self):
        """
        优化查询：
        - prefetch_related：一次性取出图片数据
        - only()：只加载必要字段
        - order_by('id')：确保分页稳定性
        """
        return (
            Product.objects
            .prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.only('image'))
            )
            .only('id', 'name', 'price', 'image_main', 'stock', 'description')
            .order_by('-id')
        )

    def get_context_data(self, **kwargs):
        """
        增强上下文，包含购物车信息 + 每个商品首图
        """
        context = super().get_context_data(**kwargs)
        cart_items, cart_total_count, cart_total_price = get_cart_items(self.request)
        context['cart_items'] = cart_items
        context['cart_total_count'] = cart_total_count
        context['cart_total_price'] = cart_total_price
        return context


# =======================
# 商品详情页
# =======================
class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items, cart_total_count, cart_total_price = get_cart_items(self.request)
        context['cart_items'] = cart_items
        context['cart_total_count'] = cart_total_count
        context['cart_total_price'] = cart_total_price
        return context


# =======================
# 商品增删改（可扩展）
# =======================
def product_create(request):
    if request.method == 'POST':
        # 创建商品逻辑（可扩展）
        pass
    return render(request, 'products/product_form.html')


def product_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        # 更新商品逻辑（可扩展）
        pass
    return render(request, 'products/product_form.html', {'product': product})


def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        return JsonResponse({'success': True})
    return render(request, 'products/product_confirm_delete.html', {'product': product})


# =======================
# 购物车操作
# =======================
def add_to_cart(request, product_id):
    """
    将商品加入 session 购物车，默认数量 +1（可改为表单量）
    """
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {}) or {}
    pid = str(product.id)
    qty = int(request.POST.get('quantity', 1)) if request.method == 'POST' else 1
    cart[pid] = int(cart.get(pid, 0)) + max(1, qty)
    request.session['cart'] = cart
    # 如果调用处希望跳回商品详情，可用 HTTP_REFERER 或 product 列表
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    return redirect('product_list')


def remove_from_cart(request, product_id):
    """
    从购物车减少 1 或移除（POST 可传 quantity）
    """
    cart = request.session.get('cart', {}) or {}
    pid = str(product_id)
    if pid in cart:
        try:
            dec = int(request.POST.get('quantity', 1)) if request.method == 'POST' else 1
        except Exception:
            dec = 1
        cart[pid] = cart.get(pid, 0) - dec
        if cart[pid] <= 0:
            cart.pop(pid, None)
        request.session['cart'] = cart
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    return redirect('product_list')


@login_required
@require_POST
def add_review(request, product_id):
    """
    提交商品评论（登录用户）。表单字段：rating, content
    提交后重定向回 product_detail 页面。
    """
    product = get_object_or_404(Product, id=product_id)
    try:
        rating = int(request.POST.get('rating', 5))
    except Exception:
        rating = 5
    rating = max(1, min(5, rating))
    content = (request.POST.get('content') or '').strip()
    # 创建评论
    from .models import ProductReview
    ProductReview.objects.create(product=product, user=request.user, rating=rating, content=content)
    return redirect('product_detail', pk=product.id)
