"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse

from rest_framework_simplejwt.views import ( # JWT ile ilgili view'ları import et
    TokenObtainPairView, # Token alma view'ı
    TokenRefreshView, # Token yenileme view'ı
)

# iyzico callback endpoint'ini doğrudan import et (DRF router'ından bağımsız)
from payments.views import payment_callback

def health(_request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/health/', health),
    
    # Bu adrese email/password token edince 'access' ve 'refresh' token'ları alınacak. (Login)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), # Token alma endpoint'i
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # Token yenileme endpoint'i
    # Giriş yapılan bilgilere göre yetkilendirme işlemleri yapılır.

    # iyzico callback endpoint - DRF router'ından ÖNCE, tamamen public (authentication kontrolü yok)
    # Bu endpoint iyzico'dan geldiği için authentication gerektirmez
    # Farklı bir URL path kullanarak DRF authentication middleware'inden kaçınıyoruz
    path('payments/callback/', payment_callback, name='payment-callback-public'),
    
    # /api/v1/ ile başlayan tüm istekleri users.urls'e yönlendir. (Kullanıcı CRUD işlemleri için)
    
    path('api/v1/', include('users.urls')), # 'users' uygulamasının URL'lerini dahil et. users modülü.
    path('api/v1/', include('appointments.urls')), # 'appointments' uygulamasının URL'lerini dahil et. appointments modülü.
    path('api/v1/', include('ventings.urls')), # 'ventings' uygulamasının URL'lerini dahil et.
    path('api/v1/', include('payments.urls')), # 'payments' uygulamasının URL'lerini dahil et.
]
