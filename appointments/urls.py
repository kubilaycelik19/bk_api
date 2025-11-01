from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AvailableTimeSlotViewSet, AppointmentViewSet

router = DefaultRouter()
# İki yeni adres seti tanımlıyoruz
router.register(r'slots', AvailableTimeSlotViewSet, basename='availabletimeslot')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', include(router.urls)),
]