"""
Django Signals - Randevu oluşturma/iptal işlemlerinde otomatik email gönderimi
NOT: Email gönderimi artık views.py'dan yapılıyor, signal'ler yedek olarak kaldı
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Appointment
import logging

logger = logging.getLogger(__name__)

# Email gönderimi artık views.py'dan yapılıyor (perform_create ve perform_destroy içinde)
# Signal'ler devre dışı bırakıldı çünkü duplicate email göndermemek için
# Eğer gerekirse, signal'leri tekrar aktif edebiliriz

# @receiver(post_save, sender=Appointment)
# def appointment_created_signal(sender, instance, created, **kwargs):
#     """
#     Yeni randevu oluşturulduğunda email gönder
#     NOT: Bu signal devre dışı - email gönderimi views.py'dan yapılıyor
#     """
#     pass

# @receiver(pre_delete, sender=Appointment)
# def appointment_cancelled_signal(sender, instance, **kwargs):
#     """
#     Randevu silinmeden önce (iptal edildiğinde) email gönder
#     NOT: Bu signal devre dışı - email gönderimi views.py'dan yapılıyor
#     """
#     pass

