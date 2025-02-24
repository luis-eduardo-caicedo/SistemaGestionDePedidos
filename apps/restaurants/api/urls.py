from django.urls import path
from django.views.decorators.cache import cache_page
from .views import (ListAllRestaurantView,
                    UpdateRestaurantView,
                    RestaurantView,
                    ProductItemListCreateView,
                    ProductItemUpdateDeleteView,
                    MenuRestaurantView)


urlpatterns = [
    path('', cache_page(60 * 5, cache='default')(RestaurantView.as_view()), name='list_resturantowner'),
    path('all', cache_page(60 * 5, cache='default')(ListAllRestaurantView.as_view()), name='list_resturant'),
    path('<int:pk>', UpdateRestaurantView.as_view(), name='udpate_resturant'),
    path('product-items/', cache_page(60 * 2, cache='default')(ProductItemListCreateView.as_view()), name='productitem-list-create'),
    path('product-items/<int:pk>', ProductItemUpdateDeleteView.as_view(), name='productitem-update-delete'),
    path('menu/<int:restaurant_id>', cache_page(60 * 10, cache='default')(MenuRestaurantView.as_view()), name='menu-restaurant'),
]