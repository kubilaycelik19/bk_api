from django.db import models
from config.settings import AUTH_USER_MODEL # Projenin ayarlarından özel kullanıcı modelini al
from decimal import Decimal

class AvailableTimeSlot(models.Model):

    psychologist = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_time = models.DateTimeField() # Randevu başlangıç zamanı
    end_time = models.DateTimeField() # Randevu bitiş zamanı
    is_booked = models.BooleanField(default=False) # Randevu dolu mu?

    def __str__(self):
        # Admin panelinde güzel görünmesi için
        return f"Psk. {self.psychologist.first_name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
class Appointment(models.Model):
    """
    Randevu modeli
    Status secenekleri:
    - pending_payment: Odeme bekleniyor
    - paid: Odendi
    - cancelled: Iptal edildi
    """
    STATUS_CHOICES = [
        ('pending_payment', 'Odeme Bekleniyor'),
        ('paid', 'Odendi'),
        ('cancelled', 'Iptal Edildi'),
    ]
    
    patient = models.ForeignKey(AUTH_USER_MODEL, related_name='patient_appointments', on_delete=models.CASCADE) # Hasta (Kullanıcı modeli ile ilişkilendirilir)
    time_slot = models.OneToOneField(AvailableTimeSlot, on_delete=models.CASCADE) # Randevu zaman dilimi (Tekil ilişki)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment', help_text='Randevu durumu')
    created_at = models.DateTimeField(auto_now_add=True) # Randevu oluşturulma zamanı
    notes = models.TextField(blank=True, null=True) # Randevu notları (isteğe bağlı)

    def __str__(self):
        return f"Randevu: {self.patient.first_name} @ {self.time_slot.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def calculate_price(self):
        """
        Randevu fiyatini hesaplar (saatlik ucrete gore)
        """
        try:
            # Randevu suresini hesapla
            duration = self.time_slot.end_time - self.time_slot.start_time
            hours = duration.total_seconds() / 3600.0  # Saat cinsinden
            
            # Saatlik ucreti al
            hourly_rate = AppointmentPrice.get_hourly_rate()
            
            # Toplam fiyat = saat sayisi * saatlik ucret
            total_price = Decimal(str(hours)) * hourly_rate
            
            return total_price
        except Exception:
            # Hata durumunda default deger dondur
            return Decimal('500.00')


class AppointmentPrice(models.Model):
    """
    Randevu saatlik ucret ayari (Singleton pattern)
    Sistemde sadece bir tane olacak
    """
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('500.00'),
        help_text='Saatlik randevu ucreti (TL)'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Son guncelleyen kullanici'
    )
    
    class Meta:
        verbose_name = 'Randevu Fiyat Ayari'
        verbose_name_plural = 'Randevu Fiyat Ayarlari'
    
    def __str__(self):
        return f'Saatlik Ucret: {self.hourly_rate} TL'
    
    def save(self, *args, **kwargs):
        """
        Singleton pattern: Sadece bir tane fiyat ayari olmasini saglar
        """
        # Eger zaten bir fiyat ayari varsa, ID'yi koru (guncelleme)
        existing = AppointmentPrice.objects.first()
        if existing and not self.pk:
            self.pk = existing.pk
        
        # Birden fazla kayit olmasini engelle
        self.__class__.objects.exclude(pk=self.pk).delete()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_hourly_rate(cls):
        """
        Saatlik ucreti dondurur, yoksa default deger dondurur
        """
        price_setting = cls.objects.first()
        if price_setting:
            return price_setting.hourly_rate
        # Ilk defa olusturuluyorsa default deger ile olustur
        default_price = cls.objects.create(hourly_rate=Decimal('500.00'))
        return default_price.hourly_rate