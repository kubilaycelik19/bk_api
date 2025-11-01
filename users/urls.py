from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# 'ModelViewSet' kullanıldığı için, adresleri otomatik oluşturan bir 'Router' kullanıyorum.

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user') #'users' adresi UserViewSet'e bağlandı.

urlpatterns = [
    path('', include(router.urls)), # Tüm router adreslerini dahil et
]