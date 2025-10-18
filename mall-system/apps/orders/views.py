from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from apps.products.models import Product
from .models import Order

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        # 只查询必要关联，按时间倒序
        qs = super().get_queryset().select_related('user', 'product').order_by('-order_date')
        if not self.request.user.is_superuser:
            qs = qs.filter(user=self.request.user)
        return qs

class OrderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def test_func(self):
        order = self.get_object()
        return self.request.user.is_superuser or order.user == self.request.user

class OrderCreateView(CreateView):
    model = Order
    fields = ['user', 'product', 'quantity', 'status']
    template_name = 'orders/order_form.html'
    success_url = reverse_lazy('order_list')

class OrderUpdateView(UpdateView):
    model = Order
    fields = ['user', 'product', 'quantity', 'status']
    template_name = 'orders/order_form.html'
    success_url = reverse_lazy('order_list')

class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'orders/order_confirm_delete.html'
    success_url = reverse_lazy('order_list')

def order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return render(request, 'orders/order_detail.html', {'order': order})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

@login_required
@require_POST
def create_order(request):
    """
    从 session['cart'] 创建订单（每个商品一条 Order），清空购物车，跳转到订单列表。
    cart 格式: { "<product_id>": <quantity>, ... }
    """
    cart = request.session.get('cart', {}) or {}
    if not cart:
        return redirect('dashboard')  # 购物车空则回到 dashboard

    created = []
    for pid, qty in list(cart.items()):
        try:
            product = Product.objects.get(pk=pid)
        except Product.DoesNotExist:
            continue
        try:
            q = int(qty)
        except Exception:
            q = 1
        if q <= 0:
            continue
        order = Order.objects.create(user=request.user, product=product, quantity=q, status='pending')
        created.append(order.id)

    # 清空 session 购物车
    request.session['cart'] = {}
    request.session.modified = True

    # 跳转到订单列表或第一个订单详情
    if created:
        return redirect('order_list')
    return redirect('dashboard')

def update_order(request, order_id):
    if request.method == 'POST':
        # Logic to update an order
        pass
    return render(request, 'orders/update_order.html', {'order_id': order_id})

def delete_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Order not found'}, status=404)
        return redirect('order_list')

    if request.method == 'POST':
        order.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('order_list')

    # GET 显示确认页
    return render(request, 'orders/order_confirm_delete.html', {'order': order})