from django.db import models
from django.contrib.auth.models import User  # Use Django's built-in User model
from django.core.validators import MinValueValidator, MaxValueValidator

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    contact = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Product(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255, default="Untitled Product")  # ✅ Default value added
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField()
    image = models.ImageField(upload_to='product/', blank=True, null=True)  

    def __str__(self):
        return self.title

class Cart(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Cart for {self.customer.user.username} - Total: {str(self.total)}"

class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='items')  # ✅ Fix: Add related_name
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    qty = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # ✅ Ensure cart is saved before calculating totals
        if not self.cart.pk:
            self.cart.save()

        self.line_total = (self.price * self.qty) - self.discount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} - {self.qty} units"

class PurchaseHeader(models.Model):  
    purchase_date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

class PurchaseDetail(models.Model):
    purchaseHeader = models.ForeignKey(PurchaseHeader, on_delete=models.CASCADE, related_name="details")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.TextField()
    qty = models.PositiveIntegerField()
    price = models.FloatField()
    discount = models.FloatField(default=0)
    line_total = models.FloatField()

class Feedback(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer_feedbacks")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_feedbacks")
    comments = models.TextField()

    # Sentiment Score (-1 = Negative, 0 = Neutral, +1 = Positive)
    sentiment_score = models.FloatField(
        default=0, validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)]
    )

    # Sentiment Choices (Optional)
    SENTIMENT_CHOICES = [
        ("Positive", "Positive 😀"),
        ("Neutral", "Neutral 😐"),
        ("Negative", "Negative 😞"),
    ]
    sentiment = models.CharField(
        max_length=50, choices=SENTIMENT_CHOICES, blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)  # ✅ Ensure this exists

    class Meta:
        unique_together = ("customer", "product")  # ✅ Prevent duplicate feedback

    def __str__(self):
        return f"Review by {self.customer.user.username} on {self.product}"
