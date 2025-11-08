from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .views import UserViewSet, get_self_details

# 'ModelViewSet' kullanıldığı için, adresleri otomatik oluşturan bir 'Router' kullanıyorum.

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user') #'users' adresi UserViewSet'e bağlandı.

urlpatterns = [
    path('', include(router.urls)), # Tüm router adreslerini dahil et
]

urlpatterns = [
    # YENİ EKLEDİK: "Ben Kimim?" endpoint'i
    path('users/me/', get_self_details, name='user-me'),

    # Router'ın URL'leri
    path('', include(router.urls)),
]