from django import forms
from .models import Customer, Product, CartItem, Feedback
from django.contrib.auth.models import User

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")

        return cleaned_data

# 🔹 Customer Form (Uses Only Relevant Fields)
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['contact', 'address']  # Removed redundant fields (name, email, status)

# 🔹 Product Form (Removed Prompt)
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['code', 'description', 'price', 'qty']  # Kept necessary fields

# 🔹 AI Product Description Form (Standalone)
class ProductAIForm(forms.Form):
    prompt = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter prompt for AI description'})
    )

# 🔹 Cart Item Form (Added Stock Validation)
class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['qty', 'discount']

    def clean_qty(self):
        """Ensure ordered quantity does not exceed available stock."""
        qty = self.cleaned_data['qty']
        product = self.instance.product  # Get product linked to cart item

        if qty < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        if product.qty < qty:
            raise forms.ValidationError(f"Only {product.qty} units left in stock.")

        return qty

    def clean_discount(self):
        discount = self.cleaned_data['discount']
        if discount < 0:
            raise forms.ValidationError("Discount cannot be negative.")
        return discount

# 🔹 Feedback Form (Added Custom Styling)
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['comments']
        widgets = {
            'comments': forms.Textarea(attrs={
                'placeholder': 'Your feedback...', 
                'rows': 5, 
                'class': 'form-control'
            }),
        }
