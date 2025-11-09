"""
Email gönderme servisi - Randevu bildirimleri için
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging
import threading

logger = logging.getLogger(__name__)

def _send_appointment_created_email_sync(appointment):
    """
    Randevu oluşturulduğunda hasta ve psikologa email gönder (senkron)
    """
    try:
        patient = appointment.patient
        psychologist = appointment.time_slot.psychologist
        time_slot = appointment.time_slot
        
        # Randevu bilgileri
        appointment_date = time_slot.start_time.strftime('%d %B %Y')
        appointment_time = time_slot.start_time.strftime('%H:%M')
        appointment_datetime = time_slot.start_time.strftime('%d %B %Y, %H:%M')
        
        # Hasta email'i
        patient_context = {
            'patient_name': patient.first_name + ' ' + patient.last_name if patient.first_name or patient.last_name else patient.email,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'appointment_datetime': appointment_datetime,
            'notes': appointment.notes or 'Not bırakılmadı',
            'psychologist_name': psychologist.first_name or psychologist.email,
        }
        
        patient_subject = f'Randevu Onayı - {appointment_datetime}'
        patient_message = render_to_string('emails/appointment_created_patient.txt', patient_context)
        patient_html_message = render_to_string('emails/appointment_created_patient.html', patient_context)
        
        # Psikolog email'i
        psychologist_context = {
            'psychologist_name': psychologist.first_name or psychologist.email,
            'patient_name': patient.first_name or patient.email,
            'patient_email': patient.email,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'appointment_datetime': appointment_datetime,
            'notes': appointment.notes or 'Not bırakılmadı',
        }
        
        psychologist_subject = f'Yeni Randevu - {patient.first_name or patient.email} - {appointment_datetime}'
        psychologist_message = render_to_string('emails/appointment_created_psychologist.txt', psychologist_context)
        psychologist_html_message = render_to_string('emails/appointment_created_psychologist.html', psychologist_context)
        
        # Superuser'ların email adreslerini al
        from django.contrib.auth import get_user_model
        User = get_user_model()
        superuser_emails = list(User.objects.filter(is_superuser=True, is_active=True).values_list('email', flat=True))
        
        # Email gönder - Hasta
        if patient.email:
            send_mail(
                subject=patient_subject,
                message=patient_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[patient.email],
                html_message=patient_html_message,
                fail_silently=False,
            )
            logger.info(f"Randevu oluşturma email'i gönderildi (Hasta): {patient.email}")
        
        # Email gönder - Psikolog (slot sahibi)
        if psychologist.email:
            send_mail(
                subject=psychologist_subject,
                message=psychologist_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[psychologist.email],
                html_message=psychologist_html_message,
                fail_silently=False,
            )
            logger.info(f"Randevu oluşturma email'i gönderildi (Psikolog): {psychologist.email}")
        
        # Email gönder - Tüm superuser'lar (psikolog hariç, çünkü zaten gönderdik)
        for superuser_email in superuser_emails:
            if superuser_email and superuser_email != psychologist.email:
                send_mail(
                    subject=psychologist_subject,
                    message=psychologist_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[superuser_email],
                    html_message=psychologist_html_message,
                    fail_silently=False,
                )
                logger.info(f"Randevu oluşturma email'i gönderildi (Superuser): {superuser_email}")
            
    except Exception as e:
        logger.error(f"Randevu oluşturma email'i gönderilirken hata: {str(e)}", exc_info=True)


def send_appointment_created_email(appointment):
    """
    Randevu oluşturulduğunda hasta ve psikologa email gönder (asenkron)
    Threading kullanarak arka planda çalışır, randevu oluşturma işlemini yavaşlatmaz
    """
    # Appointment objesini thread-safe bir şekilde geçirmek için ID kullan
    appointment_id = appointment.id
    
    def send_email_thread():
        try:
            # Thread içinde appointment'ı tekrar veritabanından al
            from .models import Appointment
            appointment = Appointment.objects.get(id=appointment_id)
            _send_appointment_created_email_sync(appointment)
        except Appointment.DoesNotExist:
            logger.error(f"Randevu bulunamadı (ID: {appointment_id})")
        except Exception as e:
            logger.error(f"Thread içinde email gönderilirken hata: {str(e)}", exc_info=True)
    
    # Thread'i başlat
    thread = threading.Thread(target=send_email_thread, daemon=True)
    thread.start()
    logger.info(f"Email gönderimi arka planda başlatıldı (Randevu ID: {appointment_id})")


def _send_appointment_cancelled_email_sync(appointment, cancelled_by_admin=False):
    """
    Randevu iptal edildiğinde hasta ve psikologa email gönder (senkron)
    """
    try:
        patient = appointment.patient
        psychologist = appointment.time_slot.psychologist
        time_slot = appointment.time_slot
        
        # Randevu bilgileri
        appointment_datetime = time_slot.start_time.strftime('%d %B %Y, %H:%M')
        
        # Hasta email'i
        patient_context = {
            'patient_name': patient.first_name or patient.email,
            'appointment_datetime': appointment_datetime,
            'cancelled_by_admin': cancelled_by_admin,
        }
        
        patient_subject = f'Randevu İptali - {appointment_datetime}'
        patient_message = render_to_string('emails/appointment_cancelled_patient.txt', patient_context)
        patient_html_message = render_to_string('emails/appointment_cancelled_patient.html', patient_context)
        
        # Psikolog email'i
        psychologist_context = {
            'psychologist_name': psychologist.first_name or psychologist.email,
            'patient_name': patient.first_name or patient.email,
            'appointment_datetime': appointment_datetime,
            'cancelled_by_admin': cancelled_by_admin,
        }
        
        psychologist_subject = f'Randevu İptal Edildi - {patient.first_name or patient.email} - {appointment_datetime}'
        psychologist_message = render_to_string('emails/appointment_cancelled_psychologist.txt', psychologist_context)
        psychologist_html_message = render_to_string('emails/appointment_cancelled_psychologist.html', psychologist_context)
        
        # Email gönder - Hasta
        if patient.email:
            send_mail(
                subject=patient_subject,
                message=patient_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[patient.email],
                html_message=patient_html_message,
                fail_silently=False,
            )
            logger.info(f"Randevu iptal email'i gönderildi (Hasta): {patient.email}")
        
        # Email gönder - Psikolog
        if psychologist.email:
            send_mail(
                subject=psychologist_subject,
                message=psychologist_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[psychologist.email],
                html_message=psychologist_html_message,
                fail_silently=False,
            )
            logger.info(f"Randevu iptal email'i gönderildi (Psikolog): {psychologist.email}")
            
    except Exception as e:
        logger.error(f"Randevu iptal email'i gönderilirken hata: {str(e)}", exc_info=True)


def send_appointment_cancelled_email(appointment, cancelled_by_admin=False):
    """
    Randevu iptal edildiğinde hasta ve psikologa email gönder (asenkron)
    Threading kullanarak arka planda çalışır, randevu iptal işlemini yavaşlatmaz
    
    Not: pre_delete signal'da çağrıldığı için appointment henüz silinmemiş,
    bu yüzden appointment bilgilerini önceden kaydetmemiz gerekiyor
    """
    # Appointment bilgilerini thread-safe bir şekilde kaydet
    appointment_id = appointment.id
    patient_email = appointment.patient.email if appointment.patient else None
    psychologist_email = appointment.time_slot.psychologist.email if appointment.time_slot and appointment.time_slot.psychologist else None
    appointment_datetime = appointment.time_slot.start_time.strftime('%d %B %Y, %H:%M') if appointment.time_slot else None
    patient_name = appointment.patient.first_name or appointment.patient.email if appointment.patient else None
    psychologist_name = appointment.time_slot.psychologist.first_name or appointment.time_slot.psychologist.email if appointment.time_slot and appointment.time_slot.psychologist else None
    
    def send_email_thread():
        try:
            # Bilgileri önceden kaydettik, direkt email gönder
            # Hasta email'i
            if patient_email and appointment_datetime:
                patient_context = {
                    'patient_name': patient_name,
                    'appointment_datetime': appointment_datetime,
                    'cancelled_by_admin': cancelled_by_admin,
                }
                
                patient_subject = f'Randevu İptali - {appointment_datetime}'
                patient_message = render_to_string('emails/appointment_cancelled_patient.txt', patient_context)
                patient_html_message = render_to_string('emails/appointment_cancelled_patient.html', patient_context)
                
                send_mail(
                    subject=patient_subject,
                    message=patient_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[patient_email],
                    html_message=patient_html_message,
                    fail_silently=False,
                )
                logger.info(f"Randevu iptal email'i gönderildi (Hasta): {patient_email}")
            
            # Psikolog email'i
            if psychologist_email and appointment_datetime:
                psychologist_context = {
                    'psychologist_name': psychologist_name,
                    'patient_name': patient_name,
                    'appointment_datetime': appointment_datetime,
                    'cancelled_by_admin': cancelled_by_admin,
                }
                
                psychologist_subject = f'Randevu İptal Edildi - {patient_name} - {appointment_datetime}'
                psychologist_message = render_to_string('emails/appointment_cancelled_psychologist.txt', psychologist_context)
                psychologist_html_message = render_to_string('emails/appointment_cancelled_psychologist.html', psychologist_context)
                
                send_mail(
                    subject=psychologist_subject,
                    message=psychologist_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[psychologist_email],
                    html_message=psychologist_html_message,
                    fail_silently=False,
                )
                logger.info(f"Randevu iptal email'i gönderildi (Psikolog): {psychologist_email}")
                
        except Exception as e:
            logger.error(f"Thread içinde iptal email'i gönderilirken hata: {str(e)}", exc_info=True)
    
    # Thread'i başlat
    thread = threading.Thread(target=send_email_thread, daemon=True)
    thread.start()
    logger.info(f"İptal email gönderimi arka planda başlatıldı (Randevu ID: {appointment_id})")

