from django.urls import path
from . import views

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('create/', views.create_order, name='create_order'),  # 新增：从购物车创建订单
    path('<int:order_id>/delete/', views.delete_order, name='delete_order'),
]