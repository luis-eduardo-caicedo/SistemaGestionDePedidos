from django.contrib import admin
from .models import Order, OrderItem, ReportRequest


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'restaurant', 
        'client', 
        'waitress', 
        'status_order', 
        'total', 
        'status', 
        'created_at', 
        'updated_at'
    )
    list_filter = ('restaurant', 'status_order', 'status')
    search_fields = ('restaurant__name', 'client__name', 'waitress__username')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order', 
        'product_item', 
        'quantity', 
        'price_unit', 
        'subtotal', 
        'status', 
    )
    list_filter = ('order', 'status')
    search_fields = ('order__id', 'product_item__name')


@admin.register(ReportRequest)
class ReportRequesttemAdmin(admin.ModelAdmin):
    list_display = (
        'task_id', 
        'user', 
        'status_report', 
        'report_date', 
        'created_at', 
    )
    list_filter = ('report_date', 'status_report')
    search_fields = ('report_date', 'status_report')
