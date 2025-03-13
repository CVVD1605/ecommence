# Imports
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.contrib.auth.models import User
from .forms import UserRegistrationForm
from .services import recommend_products_for_user

from .models import Customer, Product, Cart, CartItem, PurchaseHeader, PurchaseDetail, Feedback
from .forms import CustomerForm, ProductForm, FeedbackForm, CartItemForm

from transformers import pipeline
import json
import traceback
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download sentiment model only once (not at runtime)
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# Load Hugging Face pipeline globally (avoid reloading per request)
description_generator = pipeline('text-generation', model='gpt2')

# ----------------- 🔹 USER AUTHENTICATION VIEWS 🔹 -----------------

def register(request):
    """Handles new user registration."""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Hash the password
            user.save()

            # ✅ Ensure customer is created after user registration
            Customer.objects.create(user=user, name=user.username, email=user.email)

            login(request, user)  # Automatically log in the new user
            return redirect('home')  # Redirect to home page after registration
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})

@login_required
def profile(request):
    """Displays user profile details."""
    return render(request, 'profile.html', {'user': request.user})

def user_login(request):
    if request.method == "POST":
        username, password = request.POST.get('username'), request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome, {username}!")
            return redirect('home')
        messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

# ----------------- 🔹 HOME PAGE VIEW 🔹 -----------------

def home(request):
    return render(request, 'home.html', {'page_title': 'Home Page'})

# ----------------- 🔹 CRUD OPERATIONS 🔹 -----------------

@login_required
def create_customer(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('customer_list')
    return render(request, 'customer_form.html', {'form': form})

@login_required
def list_customers(request):
    return render(request, 'customer_list.html', {'customers': Customer.objects.all()})

@login_required
def update_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        return redirect('customer_list')
    return render(request, 'customer_form.html', {'form': form})

@login_required
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.delete()
        return redirect('customer_list')
    return render(request, 'customer_confirm_delete.html', {'customer': customer})

# ----------------- 🔹 PRODUCT RECOMMENDATION & GENERATION 🔹 -----------------

def generate_product_description(name):
    """Generate AI-based product descriptions."""
    prompt = f"Write a product description for {name}:"
    result = description_generator(prompt, max_length=50, num_return_sequences=1)
    return result[0]['generated_text']

def generate_description(request):
    if request.method == "POST":
        prompt = request.POST.get('prompt', '')
        if not prompt:
            return JsonResponse({"error": "Prompt is required."}, status=400)
        
        return JsonResponse({"description": generate_product_description(prompt)})
    
    return JsonResponse({"error": "Invalid request method."}, status=405)

@login_required
def create_product(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        product = form.save(commit=False)
        product.save()
        return redirect('product_list')
    return render(request, 'product_form.html', {'form': form})

@login_required
def list_products(request):
    query = request.GET.get('query', '')
    products = Product.objects.filter(description__icontains=query) if query else Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

@login_required
def update_product(request, pk):
    """Updates an existing product."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # Redirect after saving
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'product_form.html', {'form': form, 'product': product})

@login_required
def delete_product(request, pk):
    """Deletes a product."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":  # Confirm deletion via POST request
        product.delete()
        return redirect('product_list')  # Redirect after deletion
    return render(request, 'product_confirm_delete.html', {'product': product})

@login_required
def purchase_history(request):
    """View to display the purchase history of the logged-in customer."""
    try:
        customer = Customer.objects.get(user=request.user)  # Get customer linked to user
    except Customer.DoesNotExist:
        return render(request, 'error.html', {'message': "No customer profile found."})

    purchase_headers = PurchaseHeader.objects.filter(customer=customer).order_by('-purchase_date')

    return render(request, 'purchase_history.html', {'purchase_headers': purchase_headers})

@login_required
def purchase_details(request, purchase_id):
    """View to display the details of a specific purchase."""
    purchase_header = get_object_or_404(PurchaseHeader, id=purchase_id, customer=request.user.customer)
    purchase_details = PurchaseDetail.objects.filter(purchaseHeader=purchase_header)

    context = {
        'purchase_header': purchase_header,
        'purchase_details': purchase_details,
    }
    return render(request, 'purchase_details.html', context)

# ----------------- 🔹 CART FUNCTIONALITY 🔹 -----------------
@login_required
def cart_detail(request):
    """View to display cart details."""
    try:
        cart_customer, created = Customer.objects.get_or_create(user=request.user, defaults={'email': request.user.email})

        # ✅ Ensure the cart exists before accessing related fields
        cart, created = Cart.objects.get_or_create(customer=cart_customer, defaults={'total': 0})

        if created:
            cart.save()  # ✅ Ensure the cart is saved before querying items

        cart_items = CartItem.objects.filter(cart=cart)  # ✅ Make sure cart items exist
        
        print(f"🛒 Cart for {cart_customer}: {cart}")  # ✅ Debugging Print
        print(f"📦 Items in Cart: {cart_items.count()}")  # ✅ Debugging Print

        return render(request, 'cart_detail.html', {
            'cart': cart,
            'cart_items': cart_items
        })

    except Customer.DoesNotExist:
        messages.error(request, "No customer profile found. Please complete your profile.")
        return redirect('profile')

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('product_list')


@login_required
def edit_cart_item(request, cart_item_id):
    """View to edit a product quantity in the cart."""
    cart_item = get_object_or_404(CartItem, id=cart_item_id)

    if request.method == 'POST':
        form = CartItemForm(request.POST, instance=cart_item)
        if form.is_valid():
            form.save()  # Save the updated quantity and line total
            cart_item.cart.save()  # Recalculate the cart total
            return redirect('cart_detail')
    else:
        form = CartItemForm(instance=cart_item)

    return render(request, 'edit_cart_item.html', {'form': form, 'cart_item': cart_item})

@login_required
def delete_cart_item(request, cart_item_id):
    """Deletes a product from the cart."""
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    
    if request.method == "POST":  # Confirm deletion via POST request
        cart_item.delete()  # Remove cart item
        cart_item.cart.save()  # Recalculate the cart total
        return redirect('cart_detail')

    return render(request, 'cart_confirm_delete.html', {'cart_item': cart_item})

@login_required
def checkout(request):
    """Handles checkout process and finalizes the order."""
    try:
        customer = Customer.objects.get(user=request.user)
        cart = Cart.objects.get(customer=customer)

        if cart.items.count() == 0:
            messages.error(request, "Your cart is empty!")
            return redirect('cart_detail')

        # Create a purchase record
        purchase = PurchaseHeader.objects.create(
            customer=customer,
            total=cart.total,
            discount=cart.discount
        )

        # Move cart items to purchase details
        for item in cart.items.all():
            PurchaseDetail.objects.create(
                purchaseHeader=purchase,
                product=item.product,
                description=item.product.description,
                qty=item.qty,
                price=item.price,
                discount=item.discount,
                line_total=item.line_total
            )

        # Clear cart
        cart.items.all().delete()
        cart.total = 0
        cart.discount = 0
        cart.save()

        messages.success(request, "Purchase successful! Your order has been placed.")
        return redirect('purchase_history')

    except Customer.DoesNotExist:
        messages.error(request, "No customer profile found.")
        return redirect('profile')

@login_required
def add_to_cart(request, product_id):  # ✅ Ensure function is defined
    """Handles adding a product to the cart."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # ✅ Ensure customer exists
            cart_customer, created = Customer.objects.get_or_create(user=request.user, defaults={'email': request.user.email})

            # ✅ Ensure product exists
            product = get_object_or_404(Product, id=product_id)

            # ✅ Ensure cart exists
            cart, created = Cart.objects.get_or_create(customer=cart_customer, defaults={'discount': 0, 'total': 0})
            cart.save()

            # ✅ Check if the product is already in the cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'qty': 1, 'price': product.price, 'discount': 0}
            )

            if not created:
                cart_item.qty += 1
                cart_item.save()

            # ✅ Recalculate cart total
            total = sum(item.price * item.qty for item in cart.items.all())
            discount = sum(item.discount for item in cart.items.all())

            cart.total = total
            cart.discount = discount
            cart.save()

            return JsonResponse({"success": True, "total": cart.total, "discount": cart.discount})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)

# ----------------- 🔹 FEEDBACK & SENTIMENT ANALYSIS 🔹 -----------------

def analyze_sentiment(text):
    """Analyze sentiment of a given text."""
    scores = sia.polarity_scores(text)
    return ("Positive" if scores['compound'] > 0.05 else
            "Negative" if scores['compound'] < -0.05 else "Neutral"), scores['compound']

@login_required
def submit_feedback(request, product_id):
    """Submit feedback and analyze sentiment."""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.customer = get_object_or_404(Customer, user=request.user)
            feedback.product = product
            feedback.sentiment, feedback.sentiment_score = analyze_sentiment(feedback.comments)
            feedback.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect('product_list')

    return render(request, 'submit_feedback.html', {'form': FeedbackForm(), 'product': product})

@login_required
def view_feedback(request, product_id):
    """View feedback for a product."""
    product = get_object_or_404(Product, id=product_id)
    feedback_list = Feedback.objects.filter(product=product).select_related('customer').order_by('-created_at')
    return render(request, 'feedback/view_feedback.html', {'product': product, 'feedback_list': feedback_list})
