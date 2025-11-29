from django.db import models
from config.settings import AUTH_USER_MODEL
import uuid


class Payment(models.Model):
    """
    Randevu odemesi icin payment modeli
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('processing', 'Isleniyor'),
        ('completed', 'Tamamlandi'),
        ('failed', 'Basarisiz'),
        ('cancelled', 'Iptal Edildi'),
        ('refunded', 'Iade Edildi'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.OneToOneField('appointments.Appointment', on_delete=models.CASCADE, related_name='payment')
    patient = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Odeme tutari
    currency = models.CharField(max_length=3, default='TRY')  # Para birimi
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # iyzico bilgileri
    iyzico_payment_id = models.CharField(max_length=255, blank=True, null=True)
    iyzico_conversation_id = models.CharField(max_length=255, blank=True, null=True)
    iyzico_basket_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Odeme yontemi bilgileri
    payment_method = models.CharField(max_length=50, blank=True, null=True)  # card, bank_transfer, vs.
    
    # Tarih bilgileri
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)  # Odeme yapildigi tarih
    
    # Hata mesajlari
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Odeme'
        verbose_name_plural = 'Odemeler'
    
    def __str__(self):
        return f"Odeme - {self.patient.first_name} - {self.appointment.id} - {self.status}"