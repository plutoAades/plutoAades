from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Prefetch
from .models import Product, ProductImage


# =======================
# 辅助函数：获取购物车信息
# =======================
def get_cart_items(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_count = 0
    total_price = 0
    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.filter(id__in=product_ids)
    product_map = {product.id: product for product in products}
    for pid, qty in cart.items():
        product = product_map.get(int(pid))
        if product:
            cart_items.append({'product': product, 'quantity': qty})
            total_count += qty
            total_price += product.price * qty
    return cart_items, total_count, total_price


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
    if not request.user.is_authenticated:
        return redirect('login')

    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    # 跳转回来源页面
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def remove_from_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')

    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        cart[str(product_id)] -= 1
        if cart[str(product_id)] <= 0:
            del cart[str(product_id)]
        request.session['cart'] = cart

    return redirect(request.META.get('HTTP_REFERER', 'product_list'))
