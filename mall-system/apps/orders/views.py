from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Order

class OrderListView(ListView):
    model = Order
    template_name = 'orders/order_list.html'  # 可自定义模板路径
    context_object_name = 'orders'

class OrderDetailView(DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

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

def create_order(request):
    if request.method == 'POST':
        # Logic to create an order
        pass
    return render(request, 'orders/create_order.html')

def update_order(request, order_id):
    if request.method == 'POST':
        # Logic to update an order
        pass
    return render(request, 'orders/update_order.html', {'order_id': order_id})

def delete_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        order.delete()
        return JsonResponse({'success': 'Order deleted'}, status=204)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)