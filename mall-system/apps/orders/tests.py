from django.test import TestCase
from .models import Order

class OrderModelTest(TestCase):

    def setUp(self):
        self.order = Order.objects.create(
            product_name="Test Product",
            quantity=2,
            price=100.00
        )

    def test_order_creation(self):
        self.assertEqual(self.order.product_name, "Test Product")
        self.assertEqual(self.order.quantity, 2)
        self.assertEqual(self.order.price, 100.00)

    def test_order_str(self):
        self.assertEqual(str(self.order), f"{self.order.product_name} - {self.order.quantity}")