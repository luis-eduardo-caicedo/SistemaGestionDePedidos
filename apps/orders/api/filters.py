import django_filters
from django.utils.timezone import now, timedelta
from apps.orders.models import Order


class OrderFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name="created_at", 
        lookup_expr="date__gte",
        label="Fecha de inicio (YYYY-MM-DD)"
    )
    end_date = django_filters.DateFilter(
        field_name="created_at", 
        lookup_expr="date__lte",
        label="Fecha de fin (YYYY-MM-DD)"
    )

    class Meta:
        model = Order
        fields = ['start_date', 'end_date']