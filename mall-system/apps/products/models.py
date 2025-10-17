from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.views.generic import ListView
from django.db.models import Prefetch

class Product(models.Model):
    name = models.CharField("商品名称", max_length=100, db_index=True)
    description = models.TextField("商品描述", blank=True)
    price = models.DecimalField(
        "价格", 
        max_digits=10,    # 最大整数位数 + 小数位数
        decimal_places=2, # 保留两位小数
        default=Decimal('0.00')
    )
    category = models.CharField("商品分类", max_length=50, blank=True, null=True, default="未分类")  # ✅ 新增字段
    image_main = models.ImageField("主图", upload_to='product_images/', blank=True, null=True)  # ✅ 新增字段
    stock = models.PositiveIntegerField("库存")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    detail_info = models.JSONField("详细信息(JSON)", blank=True, null=True, default=dict)  # 新增字段

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)  # 迁移后改回

# 新增：商品评论
class ProductReview(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='product_reviews', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)  # 1-5
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Review({self.product_id}) by {self.user_id}'

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Product.objects
            .prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.only('image'))
            )
            .only('id', 'name', 'price')
            .order_by('id')
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items, cart_total_count, cart_total_price = get_cart_items(self.request)
        context['cart_items'] = cart_items
        context['cart_total_count'] = cart_total_count
        context['cart_total_price'] = cart_total_price
        return context