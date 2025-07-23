from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

def home_redirect(request):
    if request.user.is_authenticated:  # 判断用户是否已登录
        return redirect('product_list')  # 如果已登录，重定向到商品列表
    return redirect('login')  # 如果未登录，重定向到登录页面

urlpatterns = [
    path('admin/', admin.site.urls),
    path('products/', include('apps.products.urls')),
    path('orders/', include('apps.orders.urls')),
    path('users/', include('apps.users.urls')),  # 确保注册了 users 路由
    path('chat/', include('apps.chat.urls')),
    path('', home_redirect, name='home'),  # 根路径处理逻辑
    path('api/products/', include('apps.products.api.urls')),
    path('api/orders/', include('apps.orders.api.urls')),
    path('api/users/', include('apps.users.api.urls')),
    path('api/chat/', include('apps.chat.api.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)