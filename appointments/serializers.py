# appointments/serializers.py

from rest_framework import serializers
from .models import AvailableTimeSlot, Appointment, AppointmentPrice
# NOT: Hastanın detaylarını (isim vb.) göstermek için UserSerializer'a ihtiyacımız var
from users.serializers import UserSerializer  # Hata yok; import doğru şekilde yapılmış.

class AvailableTimeSlotSerializer(serializers.ModelSerializer):
    """
    Müsait zaman slotlarını JSON'a çevirir.
    (Artık 'psychologist' alanı yok, daha basit)
    """
    class Meta:
        model = AvailableTimeSlot
        fields = ['id', 'start_time', 'end_time', 'is_booked']


class AppointmentPriceSerializer(serializers.ModelSerializer):
    """
    Randevu fiyat ayari serializer
    """
    class Meta:
        model = AppointmentPrice
        fields = ['id', 'hourly_rate', 'updated_at', 'updated_by']
        read_only_fields = ['id', 'updated_at']


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Hastanın aldığı randevuları JSON'a çevirir.
    """
    # 'patient' ve 'time_slot' alanları normalde 'id' olarak görünür.
    # Biz bu 'id' yerine, o 'id'ye ait objenin tüm detaylarını
    # iç içe (nested) göstermek için ilişkili Serializer'ları kullanıyoruz.
    patient = UserSerializer(read_only=True, allow_null=True)
    time_slot = AvailableTimeSlotSerializer(read_only=True, allow_null=True)
    
    # Payment bilgisini SerializerMethodField ile al (circular import'u onlemek icin)
    payment = serializers.SerializerMethodField()
    # Randevu fiyati (hesaplanmis)
    calculated_price = serializers.SerializerMethodField()
    
    def to_representation(self, instance):
        """
        Randevu serialize edilirken, eğer time_slot veya patient silinmişse
        veya bozuk bir ilişki varsa, güvenli bir şekilde işle.
        """
        try:
            # Normal serialization'ı dene
            representation = super().to_representation(instance)
            
            # Eğer time_slot None ise veya ilişki bozuksa
            if not representation.get('time_slot'):
                representation['time_slot'] = None
            
            # Eğer patient None ise veya ilişki bozuksa
            if not representation.get('patient'):
                representation['patient'] = None
            
            # Eğer kritik alanlar eksikse, serialization hatası fırlat
            # Böylece view'da bu randevu filtrelenecek
            if not representation.get('time_slot') or not representation.get('id'):
                raise serializers.ValidationError("Randevu serialization hatası: Eksik ilişki verileri")
                
            return representation
        except Exception as e:
            # Serialization sırasında bir hata olursa, ValidationError fırlat
            # Bu durumda view bu randevuyu atlayacak
            print(f"AppointmentSerializer hatası (ID: {getattr(instance, 'id', 'unknown')}): {str(e)}")
            raise serializers.ValidationError(f"Randevu serialization hatası: {str(e)}")

    def get_payment(self, obj):
        """
        Payment bilgisini serialize et (circular import'u onlemek icin)
        Payment tablosu yoksa veya payment yoksa None dondurur
        """
        try:
            # Payment tablosu var mi kontrol et
            from payments.models import Payment
            if hasattr(obj, 'payment'):
                try:
                    payment = obj.payment
                    if payment:
                        return {
                            'id': str(payment.id),
                            'status': payment.status,
                            'amount': str(payment.amount),
                            'currency': payment.currency,
                            'created_at': payment.created_at.isoformat() if payment.created_at else None,
                            'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
                        }
                except (AttributeError, Exception) as e:
                    # Payment iliskisi yoksa veya hata varsa None dondur
                    return None
        except (ImportError, Exception):
            # Payment modeli yoksa veya tablo yoksa None dondur
            return None
        return None
    
    def get_calculated_price(self, obj):
        """
        Randevu fiyatini hesaplar ve dondurur
        """
        try:
            price = obj.calculate_price()
            return str(price)
        except Exception:
            return None
    
    # Hastanın randevu alırken (POST) hangi slotu istediğini
    # bize 'id' olarak göndermesi için bu alanı ekliyoruz.
    # 'write_only=True' = Bu alan sadece POST/PUT ile veri ALIRKEN kullanılır,
    # GET ile veri GÖSTERİRKEN kullanılmaz.
    time_slot_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 
            'patient',      # Okumak için (Detaylı Obje)
            'time_slot',    # Okumak için (Detaylı Obje)
            'time_slot_id', # Yazmak için (Sadece ID)
            'status',       # Randevu durumu (pending_payment, paid, cancelled)
            'payment',      # Odeme bilgisi (varsa)
            'calculated_price',  # Hesaplanan fiyat
            'created_at', 
            'notes'
        ]
        read_only_fields = ['status']  # Status sadece backend'de guncellenir