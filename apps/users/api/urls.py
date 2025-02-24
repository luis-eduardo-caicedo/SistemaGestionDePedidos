from django.urls import path
from django.views.decorators.cache import cache_page
from .views import (UserRegistrationView,
                    PasswordChangeView,
                    CustomTokenObtainPairView,
                    CustomTokenRefreshView,
                    UserListAPIView,
                    UserDetailAPIView,
                    ClientCreateAPIView,
                    ClientListAPIView,
                    ClientDetailAPIView,
                    BulkClientUploadAPIView,
                    BulkClientUploadStatusAPIView)


urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegistrationView.as_view(), name='user_register'),
    path('change-password/', PasswordChangeView.as_view(), name='change_password'),
    path('list/', cache_page(60 * 2, cache='default')(UserListAPIView.as_view()), name='list_users'),
    path('<int:pk>', UserDetailAPIView.as_view(), name='user-detail'),
    path('clients/', ClientCreateAPIView.as_view(), name='create_client'),
    path('clients/list/', cache_page(60 * 5, cache='default')(ClientListAPIView.as_view()), name='list_client'),
    path('clients/<int:pk>/', ClientDetailAPIView.as_view(), name='list_client'),
    path('clients/bulk-upload/', BulkClientUploadAPIView.as_view(), name='client-bulk-upload'),
    path('clients/bulk-upload/status/', BulkClientUploadStatusAPIView.as_view(), name='bulk-client-upload-status'),
]