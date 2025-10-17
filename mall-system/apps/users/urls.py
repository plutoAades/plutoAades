from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),  # existing
    path('profile/', views.user_profile, name='profile'),       # <-- 新增别名，修复 NoReverseMatch
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('category/<str:category>/', views.category_view, name='category_view'),
    path('stats/', views.dashboard_stats, name='dashboard_stats'),
]