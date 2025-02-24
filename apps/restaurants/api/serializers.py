from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from apps.restaurants.models import Restaurant, ProductItem
from ...users.models import User


class RestaurantSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='OWNER'))

    class Meta:
        model = Restaurant
        fields = ['id', 'owner', 'name', 'address', 'phone']


class ListRestaurantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'address', 'phone']        


class EditRestaurantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Restaurant
        fields = ['address', 'phone']


class ProductItemSerializer(serializers.ModelSerializer):

    restaurant = serializers.PrimaryKeyRelatedField(queryset=Restaurant.objects.all())

    class Meta:
        model = ProductItem
        fields = ['id', 'restaurant', 'name', 'description', 'price']


class EditProductItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductItem
        fields = ['name', 'description', 'price']