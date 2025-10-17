from decimal import Decimal
from django.db import models
from apps.users.models import User
from apps.products.models import Product

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], default='pending')

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    @property
    def total_price(self):
        """
        订单总价（适用于单商品 Order）：product.price * quantity
        返回 Decimal，模板可直接用 {{ order.total_price|floatformat:2 }}
        """
        try:
            price = getattr(self.product, 'price', None) or Decimal('0.00')
            # 如果 price 是字符串/float/Decimal，转为 Decimal
            price = Decimal(price)
            qty = int(self.quantity or 0)
            return price * qty
        except Exception:
            return Decimal('0.00')

    @property
    def created_at(self):
        """兼容模板中使用的 created_at 名称（映射到 order_date）"""
        return self.order_date

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} x {self.quantity}"