# appointments/serializers.py

from rest_framework import serializers
from .models import AvailableTimeSlot, Appointment
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


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Hastanın aldığı randevuları JSON'a çevirir.
    """
    # 'patient' ve 'time_slot' alanları normalde 'id' olarak görünür.
    # Biz bu 'id' yerine, o 'id'ye ait objenin tüm detaylarını
    # iç içe (nested) göstermek için ilişkili Serializer'ları kullanıyoruz.
    patient = UserSerializer(read_only=True, allow_null=True)
    time_slot = AvailableTimeSlotSerializer(read_only=True, allow_null=True)
    
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
            'created_at', 
            'notes'
        ]