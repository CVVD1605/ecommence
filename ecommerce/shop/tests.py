from django.test import TestCase
from django.contrib.auth.models import User
from shop.models import Product, Customer, PurchaseHeader, PurchaseDetail
from shop.services import recommend_products_for_user  # Import recommendation function

class RecommendationTests(TestCase):
    
    def setUp(self):
        """Set up test data for recommendations"""
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.customer = Customer.objects.create(user=self.user, email="testuser@email.com")

        # ✅ Ensure Product model fields match the database
        self.product1 = Product.objects.create(code="P001", description="Product 1", price=10.0, qty=10)
        self.product2 = Product.objects.create(code="P002", description="Product 2", price=20.0, qty=5)
        self.product3 = Product.objects.create(code="P003", description="Product 3", price=30.0, qty=15)

        # ✅ Ensure we are using the correct foreign key name from PurchaseDetail model
        purchase_header = PurchaseHeader.objects.create(customer=self.customer, total=60)

        # ✅ Fix: Use the correct field name `purchaseHeader`
        PurchaseDetail.objects.create(
            purchaseHeader=purchase_header, product=self.product1, description="Test Desc 1", qty=1, price=10, line_total=10
        )
        PurchaseDetail.objects.create(
            purchaseHeader=purchase_header, product=self.product2, description="Test Desc 2", qty=1, price=20, line_total=20
        )
        PurchaseDetail.objects.create(
            purchaseHeader=purchase_header, product=self.product3, description="Test Desc 3", qty=1, price=30, line_total=30
        )

    def test_recommend_products_for_user(self):
        """Test if the recommendation function returns relevant products"""
        recommendations = recommend_products_for_user(self.user)

        self.assertGreater(len(recommendations), 0, "❌ No recommendations returned!")
        self.assertIn(self.product1, recommendations, "❌ Product1 should be recommended!")
        self.assertIn(self.product2, recommendations, "❌ Product2 should be recommended!")
        print("✅ Recommendation test passed successfully!")
