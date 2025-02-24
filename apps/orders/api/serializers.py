from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from ..models import OrderItem, Order, ReportRequest


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_item', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'client', 'waitress', 'status_order', 'total', 'items'
        ]
        read_only_fields = ['total', 'status_order', 'waitress']

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError({
                "detail": "Authentication credentials were not provided."
            })
        user = request.user

        if user.role != 'WAITRESS':
            raise serializers.ValidationError({"detail": "Only WAITRESS can create orders."})

        if not user.restaurant:
            raise serializers.ValidationError({
                "restaurant": "No restaurant is assigned to your account."
            })

        validated_data['restaurant'] = user.restaurant
        validated_data['waitress'] = user

        items_data = validated_data.pop('items')

        for item in items_data:
            product = item.get('product_item')
            if product.restaurant != user.restaurant:
                raise serializers.ValidationError({
                    "items": "All items must belong to your assigned restaurant."
                })

        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        order.update_total()

        return order
    

class ListOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'client', 'waitress', 'status_order', 'total', 'created_at', 'items'
        ]

    
class UpdateOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'restaurant', 'client', 'waitress', 'status_order',
            'total', 'items'
        ]
        read_only_fields = ['total', 'restaurant', 'waitress']

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        instance.update_total()
        return instance
    

class ReportRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportRequest
        fields = ['id', 'task_id', 'report_date', 'created_at', 'status_report']


class ReportGenerationSerializer(serializers.Serializer):
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField()


class ReportDownloadSerializer(serializers.Serializer):
    task_id = serializers.CharField()