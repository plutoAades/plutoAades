from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),  # 添加 user_profile 路由
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('category/<str:category>/', views.category_view, name='category_view'),
]