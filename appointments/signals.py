"""
Django Signals - Randevu oluşturma/iptal işlemlerinde otomatik email gönderimi
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Appointment
from .email_service import send_appointment_created_email, send_appointment_cancelled_email
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Appointment)
def appointment_created_signal(sender, instance, created, **kwargs):
    """
    Yeni randevu oluşturulduğunda email gönder
    """
    if created:
        try:
            logger.info(f"Randevu oluşturuldu, email gönderiliyor: {instance.id}")
            send_appointment_created_email(instance)
        except Exception as e:
            logger.error(f"Randevu oluşturma email'i gönderilirken hata: {str(e)}", exc_info=True)


@receiver(pre_delete, sender=Appointment)
def appointment_cancelled_signal(sender, instance, **kwargs):
    """
    Randevu silinmeden önce (iptal edildiğinde) email gönder
    """
    try:
        # Silme işlemini yapan kullanıcı admin mi kontrol et
        # (Bu bilgiyi request'ten almak için farklı bir yaklaşım gerekebilir)
        # Şimdilik genel bir kontrol yapıyoruz
        cancelled_by_admin = False
        if hasattr(instance, '_cancelled_by_admin'):
            cancelled_by_admin = instance._cancelled_by_admin
        
        logger.info(f"Randevu iptal edildi, email gönderiliyor: {instance.id}")
        send_appointment_cancelled_email(instance, cancelled_by_admin)
    except Exception as e:
        logger.error(f"Randevu iptal email'i gönderilirken hata: {str(e)}", exc_info=True)

