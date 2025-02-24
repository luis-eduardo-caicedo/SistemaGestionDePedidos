import os
import django

# Configura el entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestionPedidos.settings")
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.users.models import Client
from apps.restaurants.models import Restaurant, ProductItem
from apps.orders.models import Order, OrderItem

User = get_user_model()

def run():
    print("Iniciando la carga de datos...")

    # 1. Crear un usuario ADMIN
    admin, created = User.objects.get_or_create(
        username="admin2",
        defaults={"email": "admin@example.com", "role": "ADMIN"}
    )
    if created:
        admin.set_password("adminpassword")
        admin.save()
        print("Usuario ADMIN creado.")

    # 2. Crear un usuario WAITRESS
    waitress, created = User.objects.get_or_create(
        username="waitress",
        defaults={"email": "waitress@example.com", "role": "WAITRESS"}
    )
    if created:
        waitress.set_password("waitresspassword")
        waitress.save()
        print("Usuario WAITRESS creado.")

    # 3. Crear algunos clientes
    clients_data = [
        {"name": "Cliente Uno", "email": "cliente1@example.com", "phone": "123456789"},
        {"name": "Cliente Dos", "email": "cliente2@example.com", "phone": "987654321"},
        {"name": "Cliente Tres", "email": "cliente3@example.com", "phone": "555000111"},
    ]
    for data in clients_data:
        client, created = Client.objects.get_or_create(email=data["email"], defaults=data)
        if created:
            print(f"Cliente {client.name} creado.")

    # 4. Crear un restaurante
    restaurant, created = Restaurant.objects.get_or_create(
        name="Restaurante Central",
        defaults={
            "owner": admin,
            "address": "Calle 123",
            "phone": "555-5555",
            "status": True
        }
    )
    if created:
        print("Restaurante creado.")

    # Asignar el restaurante al usuario WAITRESS (si no estaba asignado)
    if not waitress.restaurant_id:
        waitress.restaurant = restaurant
        waitress.save(update_fields=["restaurant"])
        print("Restaurante asignado al WAITRESS.")

    # 5. Crear algunos productos para el restaurante
    products_data = [
        {"name": "Pizza", "description": "Pizza de pepperoni", "price": 10.99, "status": True},
        {"name": "Hamburguesa", "description": "Hamburguesa con queso", "price": 8.99, "status": True},
        {"name": "Ensalada", "description": "Ensalada mixta", "price": 6.50, "status": True},
        {"name": "Pasta", "description": "Pasta al pesto", "price": 9.50, "status": True},
    ]
    for data in products_data:
        product, created = ProductItem.objects.get_or_create(
            name=data["name"],
            restaurant=restaurant,
            defaults=data
        )
        if created:
            print(f"Producto {product.name} creado.")

    # 6. Crear una orden de ejemplo
    client = Client.objects.first()
    order, created = Order.objects.get_or_create(
        restaurant=restaurant,
        client=client,
        waitress=waitress,
        defaults={
            "status_order": "pending",
            "status": True,
            "total": 0,
            "created_at": timezone.now(),
            "updated_at": timezone.now()
        }
    )
    if created:
        print("Orden creada.")

    # 7. Agregar algunos ítems a la orden
    for product in ProductItem.objects.filter(restaurant=restaurant):
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            product_item=product,
            defaults={"quantity": 2}
        )
        if created:
            print(f"Ítem para {product.name} creado.")

    # Actualizar el total de la orden
    order.update_total()
    print("Datos de inicialización completados.")

if __name__ == '__main__':
    run()