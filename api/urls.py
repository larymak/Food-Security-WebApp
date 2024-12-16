from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, DonorViewSet, FoodItemViewSet, DonationViewSet,
    RequestViewSet, DeliveryViewSet, DeliveryTrackingViewSet, 
    NotificationViewSet, TransactionHistoryViewSet, RecipientViewSet, 
    DonorDashboardView, RecipientDashboardView, RunMatchingAlgorithmView
)

# Initialize the router
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'donors', DonorViewSet)
router.register(r'food-items', FoodItemViewSet)
router.register(r'donations', DonationViewSet)
router.register(r'recipients', RecipientViewSet)
router.register(r'requests', RequestViewSet)
router.register(r'deliveries', DeliveryViewSet)
router.register(r'delivery-trackings', DeliveryTrackingViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'transaction-histories', TransactionHistoryViewSet)

# URL patterns
app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('donor-dashboard/', DonorDashboardView.as_view(), name='donor_dashboard'),
    path('recipient-dashboard/', RecipientDashboardView.as_view(), name='recipient_dashboard'),
    path('run-matching/', RunMatchingAlgorithmView.as_view(), name='run_matching'),
]
