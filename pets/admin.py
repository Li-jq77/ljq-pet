from django.contrib import admin
from .models import PetCategory, Dog, PetProfile, WeightRecord, Vaccination, Deworming, Reminder, Post, Comment, ProductCategory, Product, Cart, CartItem, Order, OrderItem

@admin.register(PetCategory)
class PetCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_popular", "is_published")
    list_filter = ("category", "is_popular", "is_published")
    search_fields = ("name", "description")
    list_editable = ("is_popular", "is_published")

@admin.register(PetProfile)
class PetProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "species", "breed", "owner", "is_active")
    list_filter = ("species", "is_active")
    search_fields = ("name", "breed", "owner__username")

@admin.register(WeightRecord)
class WeightRecordAdmin(admin.ModelAdmin):
    list_display = ("pet", "weight", "recorded_at")

@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ("pet", "vaccine_type", "dose_number", "administered_date")

@admin.register(Deworming)
class DewormingAdmin(admin.ModelAdmin):
    list_display = ("pet", "deworming_type", "administered_date")

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("pet", "title", "reminder_date", "is_completed")
    list_filter = ("is_completed", "reminder_type")

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "created_at")
    list_filter = ("category",)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "created_at")

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "sort_order")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_published")
    list_filter = ("category", "is_published")

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "total", "status", "created_at")
    list_filter = ("status",)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price")

