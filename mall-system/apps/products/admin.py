from django.contrib import admin
from .models import Product, ProductImage
from django.utils.html import format_html

admin.site.site_header = "商城管理后台"
admin.site.site_title = "商城管理后台"
admin.site.index_title = "欢迎使用商城管理系统"

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'price', 'stock', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    inlines = [ProductImageInline]