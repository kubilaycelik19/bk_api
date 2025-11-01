from django.shortcuts import render
from rest_framework import viewsets
from .models import CustomUser
from .serializers import UserSerializer
from django.contrib.auth.hashers import make_password

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
        serializer.save(password=hashed_password)
