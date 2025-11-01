# appointments/serializers.py

from rest_framework import serializers
from .models import AvailableTimeSlot, Appointment
# NOT: Hastanın detaylarını (isim vb.) göstermek için UserSerializer'a ihtiyacımız var
from users.serializers import UserSerializer 

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
    patient = UserSerializer(read_only=True)
    time_slot = AvailableTimeSlotSerializer(read_only=True)

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