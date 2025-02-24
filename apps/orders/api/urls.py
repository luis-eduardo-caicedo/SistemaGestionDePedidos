from django.urls import path
from django.views.decorators.cache import cache_page
from apps.orders.api.views import (OrderCreateAPIView,
                                   OrderListByRestaurantAPIView,
                                   OrderDetailAPIView,
                                   ReportGenerateAPIView,
                                   ReportDownloadAPIView,
                                   ReportRequestListAPIView)

urlpatterns = [
    path('create', OrderCreateAPIView.as_view(), name='order-create'),
    path('list/<int:restaurant_id>', cache_page(60, cache='default')(OrderListByRestaurantAPIView.as_view()), name='order-list'),
    path('<int:restaurant_id>', OrderDetailAPIView.as_view(), name='order-edit'),
    path('reports/generate/', ReportGenerateAPIView.as_view(), name='report-generate'),
    path('reports/download/', ReportDownloadAPIView.as_view(), name='report-download'),
    path('reports/requests/', ReportRequestListAPIView.as_view(), name='report-request-list'),
]   