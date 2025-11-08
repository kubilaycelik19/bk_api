from urllib import request
from django.shortcuts import render
from django.db.models import Q

from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, permissions, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, BasePermission
from rest_framework.response import Response

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
        # Gelen isteğin (POST) içinden yeni slotun başlangıç ve bitiş zamanlarını al
        new_start_time_str = request.data.get('start_time')
        new_end_time_str = request.data.get('end_time')

        # Gelen metni (string) Python'un 'datetime' objesine çevir
        # (API'miz '...Z' (ISO) formatında bekliyor)
        if not new_start_time_str or not new_end_time_str:
            raise ValidationError({"detail": "Başlangıç ve bitiş zamanları gereklidir."})
        
        try:
            new_start_time = datetime.fromisoformat(new_start_time_str.replace('Z', '+00:00'))
            new_end_time = datetime.fromisoformat(new_end_time_str.replace('Z', '+00:00'))
        except (ValueError, TypeError) as e:
            raise ValidationError({"detail": f"Geçersiz tarih formatı. ISO formatı (YYYY-AA-GGTHH:MM:SSZ) gereklidir. Hata: {str(e)}"})

        # Bitiş zamanı, başlangıç zamanından önce olamaz
        if new_end_time <= new_start_time:
            raise ValidationError({"detail": "Bitiş zamanı, başlangıç zamanından önce veya ona eşit olamaz."})

        # ÇAKIŞMA KONTROLÜ
        # Veritabanında, bu yeni zaman aralığıyla *çakışan*
        # HERHANGİ BİR slot var mı diye bak.

        # Çakışma Mantığı:
        # (Eski.Başlangıç < Yeni.Bitiş) VE (Eski.Bitiş > Yeni.Başlangıç)

        overlapping_slots = AvailableTimeSlot.objects.filter(
            Q(start_time__lt=new_end_time) & 
            Q(end_time__gt=new_start_time)
        )

        # KARAR
        if overlapping_slots.exists():
            # EĞER ÇAKIŞMA VARSA: Hata fırlat (400 Bad Request)
            raise ValidationError({"detail": "Bu zaman aralığı (veya bir kısmı) zaten başka bir müsait slot ile çakışıyor."})

        # Çakışma yoksa, ModelViewSet'in normal 'create' işlemine devam etmesine izin ver.
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        # 'serializer.save()' demeden önce, 'psychologist' alanını o an giriş yapmış olan kullanıcı olarak ata.
        serializer.save(psychologist=self.request.user)

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
        Güvenli ilişki kontrolleri ile bozuk referansları filtrele.
        """
        user = self.request.user # Giriş yapan kullanıcıyı al
        if user.is_staff: # Eğer kullanıcı psikolog (admin) ise
            # Tüm randevuları göster, ama time_slot veya patient ilişkisi bozuk olanları filtrele
            queryset = Appointment.objects.select_related('time_slot', 'patient').order_by('-created_at')
            # Bozuk ilişkileri filtrele
            return queryset.filter(time_slot__isnull=False, patient__isnull=False)
        # Değilse (yani hasta ise)
        # Sadece kendi randevularını göster, ama time_slot ilişkisi bozuk olanları filtrele
        queryset = Appointment.objects.select_related('time_slot', 'patient').filter(patient=user).order_by('-created_at')
        return queryset.filter(time_slot__isnull=False)
    
    def list(self, request, *args, **kwargs):
        """
        Randevu listesi döndürülürken, serialization hataları olan randevuları filtrele.
        Her randevuyu tek tek serialize ederken ValidationError'ları yakalar ve atlar.
        """
        try:
            # Queryset'i al
            queryset = self.filter_queryset(self.get_queryset())
            
            # Her randevuyu tek tek kontrol et ve sadece geçerli olanları ekle
            filtered_data = []
            for instance in queryset:
                try:
                    # Randevuyu serialize et - eğer ValidationError fırlatılırsa atla
                    item_serializer = self.get_serializer(instance)
                    item_data = item_serializer.data
                    
                    # Ekstra kontrol: time_slot ve patient olmalı
                    if (item_data and 
                        item_data.get('id') and 
                        item_data.get('time_slot') and 
                        item_data.get('time_slot', {}).get('start_time')):
                        filtered_data.append(item_data)
                except (ValidationError, Exception) as e:
                    # Serialization hatası - bu randevuyu atla
                    print(f"AppointmentViewSet.list: Randevu {getattr(instance, 'id', 'unknown')} atlandı: {str(e)}")
                    continue
            
            # Response oluştur
            return Response(filtered_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Genel hata durumunda boş liste döndür
            print(f"AppointmentViewSet.list hatası: {str(e)}")
            return Response([], status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        """
        Yeni randevu (POST) yaratılırken mantığı yönet.
        """
        user = self.request.user # Giriş yapan kullanıcıyı al
        # Eğer randevu alan kişi psikologun kendisiyse hata ver
        if user.is_staff: # Eğer kullanıcı psikolog (admin) ise
            raise ValidationError({"detail": "Psikologlar randevu alamaz."})

        # Hastanın bize POST ile yolladığı slot ID'sini al
        time_slot_id = serializer.validated_data.pop('time_slot_id') # Randevu slot ID'si

        try:
            # O ID'ye ait slotu bul
            slot = AvailableTimeSlot.objects.get(id=time_slot_id) # Slotu veritabanından al
        except AvailableTimeSlot.DoesNotExist:
            raise ValidationError({"detail": "Geçersiz zaman slotu ID'si. Belirtilen slot bulunamadı."})

        # Eğer slot zaten doluysa (is_booked=True) hata ver
        if slot.is_booked:
            raise ValidationError({"detail": "Bu zaman slotu zaten dolu. Lütfen başka bir slot seçin."})

        # Hata yoksa: Slotu rezerve et
        slot.is_booked = True # Slotu dolu yap
        slot.save() # Değişikliği kaydet

        # Randevuyu yarat, 'patient'ı giriş yapan kullanıcıya,
        # 'time_slot'u ise bulduğumuz slota ata.
        serializer.save(patient=user, time_slot=slot) # Randevuyu kaydet

    def perform_destroy(self, instance):
        """
        Randevu silindiğinde (DELETE) slot'un is_booked durumunu False yap.
        Böylece slot tekrar müsait hale gelir ve diğer hastalar tarafından görülebilir.
        """
        # Admin tarafından iptal edildiğini signal'a bildirmek için
        instance._cancelled_by_admin = self.request.user.is_staff
        
        try:
            # Randevu ile ilişkili slotu al - eğer slot yoksa veya bozuk ilişki varsa hata verme
            slot = instance.time_slot
            
            if slot:
                # Slot'un başlangıç zamanını kontrol et - eğer randevu tarihi geçmişse slot'u güncelleme
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                
                # Eğer randevu tarihi henüz gelmemişse (gelecek bir randevu ise), slot'u tekrar müsait yap
                if slot.start_time > now:
                    slot.is_booked = False
                    slot.save()
                    print(f"Slot {slot.id} tekrar müsait hale getirildi (is_booked=False)")
                else:
                    print(f"Randevu tarihi geçmiş ({slot.start_time}), slot durumu değiştirilmedi.")
            else:
                print(f"Uyarı: Randevu {instance.id} için time_slot bulunamadı veya silinmiş.")
        except Exception as e:
            # Slot güncelleme hatası olsa bile randevuyu silmeye devam et
            print(f"Uyarı: Randevu silinirken slot güncellenemedi: {str(e)}")
        
        # ModelViewSet'in normal destroy işlemini çağır (randevuyu sil)
        super().perform_destroy(instance)