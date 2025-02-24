from django.db import models
from ..users.models import Client, User
from ..restaurants.models import Restaurant, ProductItem


class Order(models.Model):
    """
    Modelo que representa una orden/pedido realizado en un restaurante.
    """
    restaurant = models.ForeignKey(Restaurant, related_name='orders', on_delete=models.CASCADE)
    client = models.ForeignKey(Client, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    waitress = models.ForeignKey(User, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    status_order = models.CharField(max_length=50, default='pending')
    status = models.BooleanField(default=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.restaurant.name}"

    def update_total(self):
        """
        Recalcula el total de la orden sumando los subtotales de sus items.
        """
        total = sum(item.subtotal for item in self.items.all() if item.subtotal is not None)
        self.total = total
        self.save(update_fields=['total'])


class OrderItem(models.Model):
    """
    Modelo que representa cada ítem de una orden.
    """
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_item = models.ForeignKey(ProductItem, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_unit = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.price_unit is None:
            self.price_unit = self.product_item.price
        self.subtotal = self.quantity * self.price_unit
        super().save(*args, **kwargs)
        self.order.update_total()

    def __str__(self):
        return f"{self.quantity} x {self.product_item.name} - Subtotal: {self.subtotal}"
    

class ReportRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    task_id = models.CharField(max_length=255, unique=True, blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='report_requests'
    )
    report_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status_report = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"ReportRequest {self.id} by {self.user.username}"