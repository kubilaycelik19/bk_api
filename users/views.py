from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from .models import CustomUser
from .serializers import UserSerializer
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, BasePermission

class UserViewSet(viewsets.ModelViewSet):

    """
    Kullanıcıları listeleme, oluşturma, güncelleme ve silme işlemleri için API endpoint'i.
    GET, POST, PUT, DELETE isteklerini otomatze eder.
    """

    queryset = CustomUser.objects.all() # Tüm kullanıcıları alır (Yöneteceği veriler)
    serializer_class = UserSerializer # Hangi serializer'ı kullanacağını belirtir

    def get_permissions(self):
        """
        İşleme (action) göre izinleri ata.
        """
        if self.action == 'create':
            # Eğer 'create' (POST) işlemi yapılıyorsa (yani YENİ KAYIT)
            permission_classes = [AllowAny] # Herkese izin ver
        else:
            # Diğer tüm işlemler (Listele, Sil, Güncelle, Detay Görme)
            permission_classes = [IsAdminUser] # Sadece Admin'e (Psikolog) izin ver
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):

        # POST ile gelen 'password' alanını alma işlemi
        password = serializer.validated_data.get('password')
        email = serializer.validated_data.get('email')

        # Şifreyi hash'leme işlemi
        hashed_password = make_password(password)

        # Username yoksa email'den otomatik oluştur
        # Normal kullanıcılar username belirlemek zorunda değil
        # Sadece superuser oluştururken (admin panel) username gerekli olabilir
        username = serializer.validated_data.get('username')
        if not username or username.strip() == '':
            # Email'den username oluştur (örn: user@example.com -> user)
            username = email.split('@')[0]

        # Hashlenen şifreyi serializere koyarak kaydetme işlemi
        serializer.save(
                password=hashed_password,
                username=username,
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

