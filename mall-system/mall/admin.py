from django.contrib import admin

class MyAdminSite(admin.AdminSite):
    site_header = "商城管理后台"
    site_title = "商城管理后台"
    index_title = "欢迎使用商城管理系统"

    def each_context(self, request):
        context = super().each_context(request)
        context['custom_admin_css'] = True
        return context

admin.site = MyAdminSite()

# 在 apps/products/admin.py 继续正常注册模型

