import django_filters
from apps.users.models import User, Client


class UserFilter(django_filters.FilterSet):
    role = django_filters.CharFilter(field_name='role', lookup_expr='iexact')
    username = django_filters.CharFilter(field_name='username', lookup_expr='icontains')
    first_name = django_filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    
    class Meta:
        model = User
        fields = ['role', 'username', 'first_name', 'last_name']


class ClientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    phone = django_filters.CharFilter(field_name="phone", lookup_expr="icontains")
    
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone']