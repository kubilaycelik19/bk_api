from rest_framework import serializers
from .models import Payment
from appointments.models import Appointment


class PaymentSerializer(serializers.ModelSerializer):
    """
    Payment serializer - Odeme bilgilerini serialize eder
    """
    # Circular import'u onlemek icin appointment serializer'ini kullanmiyoruz
    # Sadece appointment ID'sini gosteriyoruz
    appointment_id = serializers.IntegerField(source='appointment.id', read_only=True)
    appointment_id_write = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'appointment_id',
            'appointment_id_write',
            'patient',
            'amount',
            'currency',
            'status',
            'iyzico_payment_id',
            'iyzico_conversation_id',
            'iyzico_basket_id',
            'payment_method',
            'created_at',
            'updated_at',
            'paid_at',
            'error_message'
        ]
        read_only_fields = [
            'id',
            'appointment_id',
            'patient',
            'iyzico_payment_id',
            'iyzico_conversation_id',
            'iyzico_basket_id',
            'payment_method',
            'created_at',
            'updated_at',
            'paid_at',
            'error_message'
        ]


class PaymentInitSerializer(serializers.Serializer):
    """
    Odeme baslatmak icin serializer
    """
    appointment_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    def validate_appointment_id(self, value):
        """
        Randevunun hasta icin gecerli oldugunu kontrol et
        """
        try:
            appointment = Appointment.objects.get(id=value)
            if appointment.patient != self.context['request'].user:
                raise serializers.ValidationError("Bu randevu size ait degil.")
            
            # Eger zaten bir odeme varsa
            if hasattr(appointment, 'payment'):
                existing_payment = appointment.payment
                if existing_payment.status == 'completed':
                    raise serializers.ValidationError("Bu randevu icin odeme zaten yapilmis.")
            
            return value
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("Randevu bulunamadi.")
