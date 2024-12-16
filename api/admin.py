from django.contrib import admin
from .models import User, FoodItem, Donation, Request, Matching

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')
    list_filter = ('user_type',)
    search_fields = ('username', 'email')

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('food_name', 'quantity', 'unit')
    search_fields = ('name',)

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'food_item', 'quantity', 'status', 'donation_date')
    list_filter = ('status', 'donation_date')
    search_fields = ('donor__username', 'food_item__name')

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'food_item', 'quantity', 'status', 'request_date')
    list_filter = ('status', 'request_date')
    search_fields = ('recipient__username', 'food_item__name')

@admin.register(Matching)
class MatchingAdmin(admin.ModelAdmin):
    list_display = ('donation', 'request', 'matched_date')
    list_filter = ('matched_date',)
    search_fields = ('donation__donor__username', 'request__recipient__username')