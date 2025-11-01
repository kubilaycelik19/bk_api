from django.shortcuts import render
from rest_framework import viewsets
from .models import CustomUser
from .serializers import UserSerializer
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class UserViewSet(viewsets.ModelViewSet):

    """
    Kullanıcıları listeleme, oluşturma, güncelleme ve silme işlemleri için API endpoint'i.
    GET, POST, PUT, DELETE isteklerini otomatze eder.
    """

    queryset = CustomUser.objects.all() # Tüm kullanıcıları alır (Yöneteceği veriler)
    serializer_class = UserSerializer # Hangi serializer'ı kullanacağını belirtir

    def perform_create(self, serializer):

        # POST ile gelen 'password' alanını alma işlemi
        password = serializer.validated_data.get('password')

        # Şifreyi hash'leme işlemi
        hashed_password = make_password(password)

        # Hashlenen şifreyi serializere koyarak kaydetme işlemi
        serializer.save(
                password=hashed_password,
                is_patient=True, 
                is_staff=False
            )

@api_view(['GET']) # Sadece GET isteklerini kabul eden bir API view
def get_self_details(request):
    """
    Giriş yapmış kullanıcının (token'ı gönderenin)
    kendi detaylarını döndürür.
    """
    user = request.user # Token'dan kullanıcıyı al
    serializer = UserSerializer(user) # Tercümanı kullan
    return Response(serializer.data) # JSON'ı döndür

