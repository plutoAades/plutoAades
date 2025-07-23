from django.shortcuts import render,redirect, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from .models import Product

def get_cart_items(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_count = 0
    total_price = 0
    for pid, qty in cart.items():
        try:
            product = Product.objects.get(id=pid)
            cart_items.append({'product': product, 'quantity': qty})
            total_count += qty
            total_price += product.price * qty
        except Product.DoesNotExist:
            continue
    return cart_items, total_count, total_price

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print("正在渲染商品列表页面")  # 添加调试信息
        cart_items, total_count, total_price = get_cart_items(self.request)
        context['cart_items'] = cart_items
        context['cart_total_count'] = total_count
        context['cart_total_price'] = total_price
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

def product_create(request):
    if request.method == 'POST':
        # Logic to create a new product
        pass
    return render(request, 'products/product_form.html')

def product_update(request, product_id):
    product = Product.objects.get(id=product_id)
    if request.method == 'POST':
        # Logic to update the product
        pass
    return render(request, 'products/product_form.html', {'product': product})

def product_delete(request, product_id):
    product = Product.objects.get(id=product_id)
    if request.method == 'POST':
        product.delete()
        return JsonResponse({'success': True})
    return render(request, 'products/product_confirm_delete.html', {'product': product})

def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

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