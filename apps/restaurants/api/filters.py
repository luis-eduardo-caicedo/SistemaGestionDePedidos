import django_filters
from apps.restaurants.models import Restaurant, ProductItem


class RestaurantFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    owner = django_filters.NumberFilter(field_name='owner__id', lookup_expr='exact')
    created_at = django_filters.DateFromToRangeFilter(field_name='created_at')

    class Meta:
        model = Restaurant
        fields = ['name', 'status', 'owner', 'created_at']

    
class ProductItemFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    restaurant = django_filters.NumberFilter(field_name='restaurant__id', lookup_expr='exact')
    price = django_filters.RangeFilter(field_name='price')
    created_at = django_filters.DateFromToRangeFilter(field_name='created_at')

    class Meta:
        model = ProductItem
        fields = ['name', 'status', 'restaurant', 'price', 'created_at']
