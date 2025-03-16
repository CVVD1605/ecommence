#  Standard Library Imports
# import openai
import json

# Third-Party Library Imports
import google.generativeai as genai
from transformers import pipeline

# Django Core Imports
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test

# Local Imports (App-Specific)
from .models import Customer, Product, Cart, CartItem, PurchaseHeader, PurchaseDetail, Feedback
from .forms import UserRegistrationForm, CustomerForm, ProductForm, FeedbackForm, CartItemForm
from .services import recommend_products_for_user
from .utils import analyze_sentiment

genai.configure(api_key=settings.GEMINI_API_KEY)

# Load Hugging Face pipeline globally (avoid reloading per request)
description_generator = pipeline('text-generation', model='gpt2')

# ----------------- 🔹 USER AUTHENTICATION VIEWS 🔹 -----------------


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


@user_passes_test(is_superuser)
def list_customers(request):
    """ View all customers - Only for Admin/Superusers """
    if not request.user.is_superuser:
        # Restrict non-superusers
        return render(request, "403.html", status=403)

    customers = Customer.objects.all()
    return render(request, "customers/customer_list.html", {"customers": customers})


def register(request):
    """Handles new user registration."""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Hash the password
            user.set_password(form.cleaned_data['password'])
            user.save()

            # ✅ Ensure customer is created after user registration
            Customer.objects.create(
                user=user, name=user.username, email=user.email)

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
        username, password = request.POST.get(
            'username'), request.POST.get('password')
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
    """ Allow superusers to add a new customer """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to add customers.")
        return redirect("customer_list")

    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)

            # ✅ Ensure the customer is linked to a user
            # Retrieve user_id from the form
            user_id = request.POST.get("user_id")
            if user_id:
                customer.user = User.objects.get(id=user_id)
            else:
                messages.error(
                    request, "❌ Please select a user for the customer.")
                return render(request, "customers/customer_form.html", {"form": form})

            customer.save()
            messages.success(request, "✅ Customer added successfully!")
            return redirect("customer_list")
        else:
            messages.error(
                request, "❌ Failed to add customer. Please check the form.")

    else:
        form = CustomerForm()

    return render(request, "customers/customer_form.html", {"form": form})


@login_required
def edit_customer(request, customer_id):
    """ Update only contact and address fields for a customer (Inline Editing) """
    if request.method == "POST":
        try:
            customer = get_object_or_404(Customer, id=customer_id)

            # ✅ Ensure only the owner or superuser can edit
            if request.user != customer.user and not request.user.is_superuser:
                return JsonResponse({"error": "Unauthorized"}, status=403)

            # ✅ Parse JSON request body
            data = json.loads(request.body)
            customer.contact = data.get("contact", customer.contact)
            customer.address = data.get("address", customer.address)
            customer.save()

            return JsonResponse({"success": True, "contact": customer.contact, "address": customer.address})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@login_required
def update_customer(request, customer_id):
    """ Update only contact and address fields for a customer """
    customer = get_object_or_404(Customer, id=customer_id)

    # ✅ Ensure only the owner or superuser can edit
    if request.user != customer.user and not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)  # ✅ Parse JSON request body
            customer.contact = data.get("contact", customer.contact)
            customer.address = data.get("address", customer.address)
            customer.save()

            return JsonResponse({"success": True})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)
# def update_customer(request, pk):
#     customer = get_object_or_404(Customer, pk=pk)
#     if request.method == 'POST':
#         form = CustomerForm(request.POST, instance=customer)
#         if form.is_valid():
#             form.save()
#             return redirect('customer_list')
#     else:
#         form = CustomerForm(instance=customer)
#     return render(request, 'update_customer.html', {'form': form})


@login_required
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.delete()
        return redirect('customer_list')
    return render(request, 'customer_confirm_delete.html', {'customer': customer})

# ----------------- 🔹 PRODUCT RECOMMENDATION & GENERATION 🔹 -----------------


@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_input = data.get("message", "")

            if not user_input:
                return JsonResponse({"error": "Message cannot be empty"}, status=400)

            # ✅ Use the correct Gemini model
            model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
            response = model.generate_content(user_input)

            return JsonResponse({"response": response.text})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def generate_product_description(name):
    """Generate AI-based product descriptions."""
    prompt = f"Write a product description for {name}:"
    result = description_generator(
        prompt, max_length=50, num_return_sequences=1)
    return result[0]['generated_text']


@csrf_exempt  # Disable CSRF protection for this view)
def generate_description(request):
    """AI-powered product description generator."""
    if request.method == "POST":
        try:
            # ✅ Handle both JSON and form-data requests
            if request.content_type == "application/json":
                data = json.loads(request.body)
                prompt = data.get('prompt', '')
            else:
                prompt = request.POST.get('prompt', '')

            if not prompt:
                return JsonResponse({"error": "Prompt is required."}, status=400)

            # ✅ Use Hugging Face GPT-2 model to generate text
            generator = pipeline('text-generation', model='gpt2')
            result = generator(prompt, max_length=50, num_return_sequences=1)
            generated_description = result[0]['generated_text']

            return JsonResponse({"description": generated_description})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@login_required
def create_product(request):
    """ Allow only superusers to add products """
    if not request.user.is_superuser:
        return redirect("product_list")  # Normal users get redirected

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES) #handles file uploads
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Product added successfully!")
            return redirect("product_list")
    else:
        form = ProductForm()

    return render(request, "products/product_form.html", {"form": form})


@login_required
def list_products(request):
    query = request.GET.get('query', '')
    products = Product.objects.filter(
        description__icontains=query) if query else Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

@login_required
def update_product(request, product_id):
    """View to edit a product"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Product updated successfully!")
            return redirect("product_list")
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = ProductForm(instance=product)

    return render(request, "products/product_form.html", {"form": form, "product": product})  


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
        # Get customer linked to user
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        return render(request, 'error.html', {'message': "No customer profile found."})

    purchase_headers = PurchaseHeader.objects.filter(
        customer=customer).order_by('-purchase_date')

    return render(request, 'purchase_history.html', {'purchase_headers': purchase_headers})


@login_required
def purchase_details(request, purchase_id):
    """View to display the details of a specific purchase."""
    purchase_header = get_object_or_404(
        PurchaseHeader, id=purchase_id, customer=request.user.customer)
    purchase_details = PurchaseDetail.objects.filter(
        purchaseHeader=purchase_header)

    context = {
        'purchase_header': purchase_header,
        'purchase_details': purchase_details,
    }
    return render(request, 'purchase_details.html', context)

# ----------------- 🔹 CART FUNCTIONALITY 🔹 -----------------

@login_required
def cart_detail(request):
    """View to display cart details and AI recommendations."""
    try:
        # ✅ Ensure customer exists
        cart_customer, created = Customer.objects.get_or_create(
            user=request.user, defaults={'email': request.user.email})

        # ✅ Ensure cart exists
        cart, created = Cart.objects.get_or_create(
            customer=cart_customer, defaults={'total': 0})

        if created:
            cart.save()

        cart_items = cart.items.all()

        # ✅ AI-Powered Recommendations
        recommended_products = recommend_products_for_user(request.user)

        return render(request, 'cart_detail.html', {
            'cart': cart,
            'cart_items': cart_items,
            # ✅ Pass recommendations to template
            'recommended_products': recommended_products
        })

    except Customer.DoesNotExist:
        messages.error(
            request, "⚠️ No customer profile found. Please register first.")
        print("❌ Error: No customer profile found for user:",
              request.user.username)  # ✅ Debug print
        return redirect('register')

    except Exception as e:
        messages.error(request, f"⚠️ An error occurred: {str(e)}")
        print(f"❌ Error in cart_detail(): {str(e)}")  # ✅ Debug print
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

        messages.success(
            request, "Purchase successful! Your order has been placed.")
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
            cart_customer, created = Customer.objects.get_or_create(
                user=request.user, defaults={'email': request.user.email})

            # ✅ Ensure product exists
            product = get_object_or_404(Product, id=product_id)

            # ✅ Ensure cart exists
            cart, created = Cart.objects.get_or_create(
                customer=cart_customer, defaults={'discount': 0, 'total': 0})
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

@login_required
def submit_feedback(request, product_id):
    """Allow customers to submit feedback for a product."""
    product = get_object_or_404(Product, id=product_id)

    try:
        customer = Customer.objects.get(user=request.user)  # ✅ Ensure customer exists
    except Customer.DoesNotExist:
        messages.error(request, "⚠️ No customer profile found. Please register first.")
        return redirect('register')

    # ✅ Prevent duplicate feedback
    if Feedback.objects.filter(customer=customer, product=product).exists():
        messages.error(request, "⚠️ You have already submitted feedback for this product!")
        return redirect('product_detail', product_id=product.id)

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.customer = customer
            feedback.product = product
            feedback.save()
            messages.success(request, "✅ Thank you for your feedback!")
            return redirect('product_detail', product_id=product.id)  # ✅ Redirect to product page
        else:
            messages.error(request, "❌ Invalid form submission. Please correct the errors.")

    else:
        form = FeedbackForm()

    return render(request, "shop/submit_feedback.html", {"form": form, "product": product})

@login_required
def view_feedback(request, product_id):
    """View feedback for a specific product."""
    product = get_object_or_404(Product, id=product_id)

    feedbacks = Feedback.objects.filter(product=product).order_by("-created_at")  # ✅ Sorting latest first

    return render(request, "feedback/view_feedback.html", {"product": product, "feedbacks": feedbacks})

def product_detail(request, product_id):
    """View details of a product."""
    product = get_object_or_404(Product, id=product_id)
    return render(request, "products/product_details.html", {"product": product})
