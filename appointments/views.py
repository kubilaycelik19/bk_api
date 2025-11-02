from urllib import request
from django.shortcuts import render
from django.db.models import Q

from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, permissions, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, BasePermission
from rest_framework.response import Response

from users import serializers
from .models import AvailableTimeSlot, Appointment
from .serializers import AvailableTimeSlotSerializer, AppointmentSerializer

from datetime import datetime

# --- Permission Sınıfları ---

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Sadece admin oluşturma/düzenleme/silme işlemlerini yapabilir.
    Herkes (Hastalar) sadece okuyabilir.
    """

    def has_permission(self, request, view):
        # Eğer istek 'GET', 'HEAD' or 'OPTIONS' (yani GÜVENLİ) ise, herkese izin ver.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Değilse (POST, PUT, DELETE ise), sadece admin'e (psikolog) izin ver.
        return request.user and request.user.is_staff # Sadece admin izinli
    
class IsPatientOwner(permissions.BasePermission):

    """
    Objeyi (randevuyu) sadece hastanın kendisi görebilir/silebilir.
    """
    def has_object_permission(self, request, view, obj):
        # Admin (psikolog) her şeyi görebilir
        if request.user.is_staff:
            return True
        # Eğer randevu objesi, giriş yapan hastaya aitse izin ver
        return obj.patient == request.user # Sadece kendi randevusunu görebilir/silebilir

class IsAuthenticatedOrOptions(BasePermission):
    """
    Gelen istek 'OPTIONS' ise her zaman izin ver.
    Diğer tüm istekler için 'IsAuthenticated' (Giriş yapmış mı?) kontrolü yap.
    """
    def has_permission(self, request, view):
        # Uçuş öncesi (Preflight) OPTIONS isteğine her zaman izin ver
        if request.method == 'OPTIONS':
            return True
        # Diğer tüm istekler için (GET, POST, DELETE) token'ı kontrol et
        return request.user and request.user.is_authenticated

# Buraya kadar olan kısım permission sınıfları içindi.
# Bu sınıfların döndürdüğü değerler şöyledir:
# IsAdminOrReadOnly: Sadece admin (psikolog) oluşturma/düzenleme/silme yapabilir, herkes sadece okuyabilir.
# IsPatientOwner: Sadece randevuyu alan hasta kendisi görebilir/silebilir, admin (psikolog) her şeyi görebilir.

# Classların döndürdüğü değerler viewsetlerde kullanılır.

# --- VİEWSETLER ---

class AvailableTimeSlotViewSet(viewsets.ModelViewSet):
    """
    Müsait Zaman Slotları:
    - Admin (Psikolog) Yaratır/Siler/Günceller (POST, PUT, DELETE)
    - Herkes (Hasta) Listeler (GET)
    """
    # Sadece rezerve EDİLMEMİŞ slotları listele
    queryset = AvailableTimeSlot.objects.filter(is_booked=False) # Sadece boş slotlar
    serializer_class = AvailableTimeSlotSerializer # Hangi serializer kullanılacak?

    # YENİ: Kendi özel iznimizi ekledik
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly] # Kimlik doğrulama ve özel izin.

    def create(self, request, *args, **kwargs):
        # 1. Gelen isteğin (POST) içinden yeni slotun
        #    başlangıç ve bitiş zamanlarını al
        new_start_time_str = request.data.get('start_time')
        new_end_time_str = request.data.get('end_time')

        # 2. Gelen metni (string) Python'un 'datetime' objesine çevir
        #    (API'miz '...Z' (ISO) formatında bekliyor)
        try:
            new_start_time = datetime.fromisoformat(new_start_time_str.replace('Z', '+00:00'))
            new_end_time = datetime.fromisoformat(new_end_time_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            raise ValidationError({"detail": "Geçersiz tarih formatı. ISO formatı (YYYY-AA-GGTHH:MM:SSZ) gereklidir."})

        # 3. KURAL: Bitiş zamanı, başlangıç zamanından önce olamaz
        if new_end_time <= new_start_time:
            raise ValidationError({"detail": "Bitiş zamanı, başlangıç zamanından önce veya ona eşit olamaz."})

        # 4. ÇAKIŞMA KONTROLÜ (İşin kalbi)
        # Veritabanında, bu yeni zaman aralığıyla *çakışan*
        # HERHANGİ BİR slot var mı diye bak.

        # Çakışma Mantığı (Açıklama):
        # (Eski.Başlangıç < Yeni.Bitiş) VE (Eski.Bitiş > Yeni.Başlangıç)
        # Bu sihirli formül, tüm çakışma (overlap) senaryolarını yakalar.

        overlapping_slots = AvailableTimeSlot.objects.filter(
            Q(start_time__lt=new_end_time) & 
            Q(end_time__gt=new_start_time)
        )

        # 5. KARAR
        if overlapping_slots.exists():
            # EĞER ÇAKIŞMA VARSA: Hata fırlat (400 Bad Request)
            raise ValidationError({"detail": "Bu zaman aralığı (veya bir kısmı) zaten başka bir müsait slot ile çakışıyor."})

        # 6. DEVAM ET
        # Çakışma yoksa, ModelViewSet'in normal 'create'
        # (yaratma) işlemine devam etmesine izin ver.
        return super().create(request, *args, **kwargs)

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    Randevular:
    - Hasta: Yaratır (POST), Kendi randevularını Listeler (GET), Kendi randevusunu Siler (DELETE)
    - Psikolog (Admin): Tüm randevuları Listeler (GET), Tüm randevuları Siler (DELETE)
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticatedOrOptions, IsPatientOwner] # Korumaları ekledik

    def get_queryset(self): # queryset = Appointment.objects.all()
        """
        Giriş yapan kullanıcıya göre listeyi filtrele.
        """
        user = self.request.user # Giriş yapan kullanıcıyı al
        if user.is_staff: # Eğer kullanıcı psikolog (admin) ise
            return Appointment.objects.all().order_by('-created_at') # Tüm randevuları göster
        # Değilse (yani hasta ise)
        return Appointment.objects.filter(patient=user).order_by('-created_at') # Sadece kendi randevularını göster

    def perform_create(self, serializer):
        """
        Yeni randevu (POST) yaratılırken mantığı yönet.
        """
        user = self.request.user # Giriş yapan kullanıcıyı al
        # Eğer randevu alan kişi psikologun kendisiyse hata ver
        if user.is_staff: # Eğer kullanıcı psikolog (admin) ise
            raise serializers.ValidationError("Psikologlar randevu alamaz.")

        # Hastanın bize POST ile yolladığı slot ID'sini al
        time_slot_id = serializer.validated_data.pop('time_slot_id') # Randevu slot ID'si

        try:
            # O ID'ye ait slotu bul
            slot = AvailableTimeSlot.objects.get(id=time_slot_id) # Slotu veritabanından al
        except AvailableTimeSlot.DoesNotExist:
            raise serializers.ValidationError("Geçersiz zaman slotu ID'si.") # Eğer slot yoksa hata ver

        # Eğer slot zaten doluysa (is_booked=True) hata ver
        if slot.is_booked:
            raise serializers.ValidationError("Bu zaman slotu zaten dolu.") # Eğer slot doluysa hata ver

        # Hata yoksa: Slotu rezerve et
        slot.is_booked = True # Slotu dolu yap
        slot.save() # Değişikliği kaydet

        # Randevuyu yarat, 'patient'ı giriş yapan kullanıcıya,
        # 'time_slot'u ise bulduğumuz slota ata.
        serializer.save(patient=user, time_slot=slot) # Randevuyu kaydet
