from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, payment_callback

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    # Callback endpoint'i artık config/urls.py'de doğrudan tanımlı (DRF router'ından bağımsız)
]
