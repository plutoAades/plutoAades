from django.test import TestCase
from .models import Product

class ProductModelTest(TestCase):

    def setUp(self):
        self.product = Product.objects.create(
            name='Test Product',
            price=10.99,
            description='A product for testing purposes',
            stock=100
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.price, 10.99)
        self.assertEqual(self.product.description, 'A product for testing purposes')
        self.assertEqual(self.product.stock, 100)

    def test_product_str(self):
        self.assertEqual(str(self.product), 'Test Product')