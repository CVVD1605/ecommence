from django.contrib import admin
from .models import Customer, Feedback

# ✅ Step 1: Create an Inline Admin for Feedback
class FeedbackInline(admin.TabularInline):  # Use StackedInline for a different layout
    model = Feedback
    extra = 0  # No extra empty rows
    fields = ("product", "comments", "sentiment", "created_at")  # Show these fields
    readonly_fields = ("created_at",)  # Make timestamp read-only
    ordering = ["-created_at"]  # Show latest feedback first

# ✅ Step 2: Add FeedbackInline to CustomerAdmin
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "contact")  # Fields shown in Customer list
    search_fields = ("user__username", "email")  # Enable search
    inlines = [FeedbackInline]  # Add FeedbackInline to CustomerAdmin

# ✅ Step 3: Register the Admin
admin.site.register(Customer, CustomerAdmin)
