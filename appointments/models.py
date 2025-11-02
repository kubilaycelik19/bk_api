from django.db import models
from config.settings import AUTH_USER_MODEL # Projenin ayarlarından özel kullanıcı modelini al

class AvailableTimeSlot(models.Model):

    psychologist = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_time = models.DateTimeField() # Randevu başlangıç zamanı
    end_time = models.DateTimeField() # Randevu bitiş zamanı
    is_booked = models.BooleanField(default=False) # Randevu dolu mu?

    def __str__(self):
        # Admin panelinde güzel görünmesi için
        return f"Dr. {self.psychologist.first_name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
class Appointment(models.Model):
    
    patient = models.ForeignKey(AUTH_USER_MODEL, related_name='patient_appointments', on_delete=models.CASCADE) # Hasta (Kullanıcı modeli ile ilişkilendirilir)
    time_slot = models.OneToOneField(AvailableTimeSlot, on_delete=models.CASCADE) # Randevu zaman dilimi (Tekil ilişki)
    created_at = models.DateTimeField(auto_now_add=True) # Randevu oluşturulma zamanı
    notes = models.TextField(blank=True, null=True) # Randevu notları (isteğe bağlı)

    def __str__(self):
        return f"Randevu: {self.patient.first_name} @ {self.time_slot.start_time.strftime('%Y-%m-%d %H:%M')}"