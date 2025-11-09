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
        # DEBUG: Object permission check (create işlemi için obj None olabilir)
        print(f"🔐 [PERMISSION] IsPatientOwner.has_object_permission() çağrıldı - User: {request.user.email if request.user.is_authenticated else 'Anonymous'}, Obj: {obj if obj else 'None (create)'}")
        
        # Create işlemi için obj None olabilir, bu durumda izin ver
        if obj is None:
            print(f"🔐 [PERMISSION] Create işlemi - İzin veriliyor")
            return True
        
        # Admin (psikolog) her şeyi görebilir
        if request.user.is_staff:
            print(f"🔐 [PERMISSION] Admin kullanıcı - İzin veriliyor")
            return True
        # Eğer randevu objesi, giriş yapan hastaya aitse izin ver
        has_permission = obj.patient == request.user
        print(f"🔐 [PERMISSION] Patient owner check: {has_permission}")
        return has_permission

class IsAuthenticatedOrOptions(BasePermission):
    """
    Gelen istek 'OPTIONS' ise her zaman izin ver.
    Diğer tüm istekler için 'IsAuthenticated' (Giriş yapmış mı?) kontrolü yap.
    """
    def has_permission(self, request, view):
        # DEBUG: Permission check
        print(f"🔐 [PERMISSION] IsAuthenticatedOrOptions.has_permission() çağrıldı - Method: {request.method}, User: {request.user if request.user.is_authenticated else 'Anonymous'}")
        
        # Uçuş öncesi (Preflight) OPTIONS isteğine her zaman izin ver
        if request.method == 'OPTIONS':
            print(f"🔐 [PERMISSION] OPTIONS request - İzin veriliyor")
            return True
        # Diğer tüm istekler için (GET, POST, DELETE) token'ı kontrol et
        is_authenticated = request.user and request.user.is_authenticated
        print(f"🔐 [PERMISSION] İstek authenticated: {is_authenticated}")
        if not is_authenticated:
            print(f"🔐 [PERMISSION] ❌ İstek reddedildi - Kullanıcı authenticated değil")
        return is_authenticated

# --- VİEWSETLER ---

class AvailableTimeSlotViewSet(viewsets.ModelViewSet):
    """
    Müsait Zaman Slotları:
    - Admin (Psikolog) Yaratır/Siler/Günceller (POST, PUT, DELETE)
    - Herkes (Hasta) Listeler (GET)
    """
    serializer_class = AvailableTimeSlotSerializer # Hangi serializer kullanılacak?

    # YENİ: Kendi özel iznimizi ekledik
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly] # Kimlik doğrulama ve özel izin.

    def get_queryset(self):
        """
        Müsait slotları tarih ve saat sıralamasına göre döndür.
        İptal edilen slotlar da doğru sırada görünecek.
        """
        # Sadece rezerve EDİLMEMİŞ slotları listele ve tarih/saat sıralamasına göre diz
        return AvailableTimeSlot.objects.filter(is_booked=False).order_by('start_time')

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"🔵 [VIEWSET] AppointmentViewSet oluşturuldu")

    def create(self, request, *args, **kwargs):
        """
        Randevu oluşturma işlemi - Debug log'ları için override edildi
        """
        print(f"🔵 [VIEW] create() metodu çağrıldı - User: {request.user.email if request.user.is_authenticated else 'Anonymous'}")
        print(f"🔵 [VIEW] Request data: {request.data}")
        try:
            response = super().create(request, *args, **kwargs)
            print(f"🔵 [VIEW] create() başarılı - Response status: {response.status_code}")
            return response
        except Exception as e:
            print(f"🔴 [VIEW] create() hatası: {str(e)}")
            raise

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
        print(f"🟢 [VIEW] perform_create() çağrıldı")
        user = self.request.user # Giriş yapan kullanıcıyı al
        print(f"🟢 [VIEW] User: {user.email}, is_staff: {user.is_staff}")
        
        # Eğer randevu alan kişi psikologun kendisiyse hata ver
        if user.is_staff: # Eğer kullanıcı psikolog (admin) ise
            raise ValidationError({"detail": "Psikologlar randevu alamaz."})

        # Hastanın bize POST ile yolladığı slot ID'sini al
        time_slot_id = serializer.validated_data.pop('time_slot_id') # Randevu slot ID'si
        print(f"🟢 [VIEW] time_slot_id: {time_slot_id}")

        try:
            # O ID'ye ait slotu bul
            slot = AvailableTimeSlot.objects.get(id=time_slot_id) # Slotu veritabanından al
            print(f"🟢 [VIEW] Slot bulundu - ID: {slot.id}, is_booked: {slot.is_booked}")
        except AvailableTimeSlot.DoesNotExist:
            print(f"🔴 [VIEW] Slot bulunamadı - ID: {time_slot_id}")
            raise ValidationError({"detail": "Geçersiz zaman slotu ID'si. Belirtilen slot bulunamadı."})

        # Eğer slot zaten doluysa (is_booked=True) hata ver
        if slot.is_booked:
            print(f"🔴 [VIEW] Slot zaten dolu - ID: {slot.id}")
            raise ValidationError({"detail": "Bu zaman slotu zaten dolu. Lütfen başka bir slot seçin."})

        # Hata yoksa: Slotu rezerve et
        slot.is_booked = True # Slotu dolu yap
        slot.save() # Değişikliği kaydet
        print(f"🟢 [VIEW] Slot rezerve edildi - ID: {slot.id}")

        # Randevuyu yarat, 'patient'ı giriş yapan kullanıcıya,
        # 'time_slot'u ise bulduğumuz slota ata.
        print(f"🔄 [VIEW] Randevu oluşturuluyor - User: {user.email}, Slot: {slot.id}")
        print(f"🔄 [VIEW] serializer.save() çağrılmadan önce...")
        appointment = serializer.save(patient=user, time_slot=slot) # Randevuyu kaydet
        print(f"✅ [VIEW] Randevu oluşturuldu - ID: {appointment.id}")
        print(f"✅ [VIEW] Appointment.patient: {appointment.patient.email}")
        print(f"✅ [VIEW] Appointment.time_slot: {appointment.time_slot.id}")
        print(f"✅ [VIEW] Signal tetiklenmeli... (post_save signal)")
        print(f"✅ [VIEW] perform_create() tamamlandı, response dönecek...")

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