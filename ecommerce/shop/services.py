from .models import Product, PurchaseHeader, PurchaseDetail, Customer  # ✅ Ensure all models are imported

def recommend_products_for_user(user):
    """Recommends products based on user purchase history."""
    try:
        # ✅ Fetch customer linked to user
        customer = Customer.objects.get(user=user)

        # ✅ Get all purchases by this customer
        purchase_history = PurchaseHeader.objects.filter(customer=customer)

        if not purchase_history.exists():
            return []  # No recommendations if user has no purchases

        # ✅ Get purchased product IDs
        purchased_products = PurchaseDetail.objects.filter(purchaseHeader__in=purchase_history).values_list('product', flat=True)

        # ✅ Recommend products the user has NOT purchased
        recommendations = Product.objects.exclude(id__in=purchased_products)[:5]

        return list(recommendations.values('id', 'code', 'description', 'price'))

    except Customer.DoesNotExist:
        return []  # No customer found, return empty recommendations
