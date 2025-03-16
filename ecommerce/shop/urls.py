from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import edit_customer, create_customer, view_feedback, update_product, delete_product, product_detail, update_customer
from shop import views

urlpatterns = [
    # 🔹 Home & Authentication
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'), 
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # 🔹 Customers
    path('customers/', views.list_customers, name='customer_list'),
    path('customers/add/', views.create_customer, name='create_customer'),  # ✅ Ensure this exists
    path("customers/<int:customer_id>/edit/", update_customer, name="update_customer"),
    path('customers/<int:pk>/delete/', views.delete_customer, name='delete_customer'),

    # 🔹 Products
    path('products/', views.list_products, name='product_list'),
    path('products/add/', views.create_product, name='create_product'),
    path('products/<int:product_id>/edit/', views.update_product, name='update_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path('products/<int:product_id>/feedback/', view_feedback, name='view_feedback'),

    # 🔹 AI-Generated Product Descriptions
    path('generate-description/', views.generate_description, name='generate_description'),
    path('chatbot/', views.chatbot_response, name='chatbot'),


    # 🔹 Purchase History
    path('purchase-history/', views.purchase_history, name='purchase_history'),
    path('purchase-details/<int:purchase_id>/', views.purchase_details, name='purchase_details'),

    # 🔹 Cart Functionality
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/edit/<int:cart_item_id>/', views.edit_cart_item, name='edit_cart_item'),
    path('cart/delete/<int:cart_item_id>/', views.delete_cart_item, name='delete_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path("cart/update/<int:cart_item_id>/", views.update_cart_quantity, name="update_cart_quantity"),
    path("cart/remove/<int:cart_item_id>/", views.remove_cart_item, name="remove_cart_item"),

    # 🔹 Feedback & Sentiment Analysis
    path('feedback/submit_feedback/<int:product_id>/', views.submit_feedback, name='submit_feedback'),
    # path('feedback/view/<int:product_id>/', views.view_feedback, name='view_feedback'),
]
