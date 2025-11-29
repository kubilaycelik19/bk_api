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
    Yeni randevu oluşturulduğunda:
    1. Payment otomatik oluştur
    2. Email gönder
    """
    # DEBUG: Signal'in çalışıp çalışmadığını kontrol et
    print(f"🔔 [SIGNAL DEBUG] post_save signal tetiklendi - created={created}, instance_id={instance.id if hasattr(instance, 'id') else 'N/A'}")
    logger.info(f"🔔 [SIGNAL] post_save signal tetiklendi - created={created}, instance_id={instance.id if hasattr(instance, 'id') else 'N/A'}")
    
    if created:
        try:
            print(f"🔔 [SIGNAL] Yeni randevu oluşturuldu - ID: {instance.id}")
            logger.info(f"🔔 Signal tetiklendi: Randevu oluşturuldu (ID: {instance.id})")
            
            # 1. Payment otomatik oluştur (eğer yoksa)
            try:
                from payments.models import Payment
                if not hasattr(instance, 'payment'):
                    amount = instance.calculate_price()
                    payment = Payment.objects.create(
                        appointment=instance,
                        patient=instance.patient,
                        amount=amount,
                        currency='TRY',
                        status='pending'
                    )
                    logger.info(f"💰 Payment otomatik olusturuldu - ID: {payment.id}, Amount: {amount}")
                    print(f"💰 [SIGNAL] Payment otomatik olusturuldu - ID: {payment.id}, Amount: {amount}")
                else:
                    logger.info(f"💰 Payment zaten mevcut - ID: {instance.payment.id}")
            except Exception as e:
                error_msg = f"❌ Payment olusturulurken hata: {str(e)}"
                logger.error(error_msg, exc_info=True)
                print(f"❌ [SIGNAL ERROR] {error_msg}")
                # Payment olusturulamazsa email gonderimini engelleme
            
            # 2. Email gönder
            try:
                logger.info(f"📧 Hasta: {instance.patient.email}, Psikolog: {instance.time_slot.psychologist.email}")
                print(f"📧 [SIGNAL] Email gönderilecek - Hasta: {instance.patient.email}, Psikolog: {instance.time_slot.psychologist.email}")
                send_appointment_created_email(instance)
                logger.info(f"✅ Email gönderim fonksiyonu çağrıldı (Randevu ID: {instance.id})")
                print(f"✅ [SIGNAL] Email gönderim fonksiyonu tamamlandı - ID: {instance.id}")
            except Exception as e:
                error_msg = f"❌ Randevu oluşturma email'i gönderilirken hata: {str(e)}"
                print(f"❌ [SIGNAL ERROR] {error_msg}")
                logger.error(error_msg, exc_info=True)
        except Exception as e:
            error_msg = f"❌ Randevu oluşturma signal'inde genel hata: {str(e)}"
            print(f"❌ [SIGNAL ERROR] {error_msg}")
            logger.error(error_msg, exc_info=True)
    else:
        print(f"ℹ️ [SIGNAL] Randevu güncellendi (yeni oluşturulmadı) - ID: {instance.id if hasattr(instance, 'id') else 'N/A'}")


@receiver(pre_delete, sender=Appointment)
def appointment_cancelled_signal(sender, instance, **kwargs):
    """
    Randevu silinmeden önce (iptal edildiğinde):
    1. Payment durumunu 'cancelled' yap (eğer varsa)
    2. Randevu status'unu 'cancelled' yap
    3. Email gönder
    """
    try:
        # Randevu status'unu 'cancelled' olarak işaretle (silinmeden önce)
        if instance.status != 'cancelled':
            instance.status = 'cancelled'
            instance.save(update_fields=['status'])
            logger.info(f"Randevu status'u 'cancelled' olarak guncellendi - ID: {instance.id}")
        
        # Payment varsa durumunu 'cancelled' yap
        try:
            from payments.models import Payment
            if hasattr(instance, 'payment'):
                payment = instance.payment
                if payment.status not in ['completed', 'refunded']:
                    payment.status = 'cancelled'
                    payment.save()
                    logger.info(f"Payment status'u 'cancelled' olarak guncellendi - Payment ID: {payment.id}")
        except Exception as e:
            logger.error(f"Payment iptal edilirken hata: {str(e)}", exc_info=True)
            # Payment hatası email gönderimini engellememeli
        
        # Silme işlemini yapan kullanıcı admin mi kontrol et
        cancelled_by_admin = False
        if hasattr(instance, '_cancelled_by_admin'):
            cancelled_by_admin = instance._cancelled_by_admin
        
        logger.info(f"Randevu iptal edildi, email gönderiliyor: {instance.id}")
        send_appointment_cancelled_email(instance, cancelled_by_admin)
    except Exception as e:
        logger.error(f"Randevu iptal signal'inde hata: {str(e)}", exc_info=True)

