from .models import Product, PurchaseHeader, PurchaseDetail, Customer  
from django.conf import settings
# import openai

# openai.api_key = settings.OPENAI_API_KEY 

def chat_with_gpt(user_input):
    """Send user input to OpenAI API and return AI response."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Change to "gpt-3.5-turbo" if needed
            messages=[{"role": "user", "content": user_input}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"
def recommend_products_for_user(user):
    """ AI-based product recommendations for a user """
    try:
        # ✅ Debugging: Print user info
        print(f"🔍 Debug: Generating recommendations for user {user.username}")

        # ✅ Retrieve all products
        all_products = Product.objects.all()
        print(f"✅ Debug: Found {len(all_products)} total products in database.")

        # ✅ Apply your recommendation logic here
        recommended_products = all_products[:3]  # Example: Just take the first 3 products

        # ✅ Debugging: Check recommended products
        if recommended_products:
            print(f"✅ Debug: Returning {len(recommended_products)} recommended products.")
        else:
            print("⚠️ Debug: No products selected for recommendation.")

        return recommended_products

    except Exception as e:
        print(f"❌ Error in recommend_products_for_user(): {str(e)}")
        return []
