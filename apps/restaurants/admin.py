from django.contrib import admin
from .models import Restaurant, ProductItem

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'address', 'phone', 'status')


@admin.register(ProductItem)
class ProductItemtAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'name', 'description', 'price', 'status')
