from .models import Product, PurchaseHeader 

def recommend_products_for_user(user):
    """Recommends products based on user purchase history"""
    purchase_history = Purchase.objects.filter(customer__user=user)  # ✅ Fix: Link purchase to Customer model
    
    if not purchase_history.exists():
        return []  # No recommendations if user has no purchases

    purchased_products = [p.product.id for p in purchase_history]
    
    # Recommend products that the user has NOT purchased yet
    recommendations = Product.objects.exclude(id__in=purchased_products)[:5]
    
    return list(recommendations.values('id', 'name', 'description', 'price'))
