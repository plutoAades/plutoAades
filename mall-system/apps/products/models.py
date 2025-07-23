from django.db import models
from django.utils import timezone

class Product(models.Model):
    name = models.CharField("商品名称", max_length=100)
    description = models.TextField("商品描述", blank=True)
    price = models.DecimalField("价格", max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField("库存")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField("商品图片", upload_to='product_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)  # 迁移后改回