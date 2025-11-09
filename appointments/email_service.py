"""
Email gönderme servisi - Randevu bildirimleri için
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
import threading

logger = logging.getLogger(__name__)


def _send_email_sync(subject, message, from_email, recipient_list, html_message=None):
    """
    Email gönderimini senkron olarak yapan yardımcı fonksiyon
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email gönderildi: {recipient_list}")
    except Exception as e:
        logger.error(f"Email gönderilirken hata: {str(e)}", exc_info=True)


def send_appointment_created_email(appointment):
    """
    Randevu oluşturulduğunda hasta ve psikologa email gönder (asenkron)
    """
    try:
        patient = appointment.patient
        psychologist = appointment.time_slot.psychologist
        time_slot = appointment.time_slot
        
        # Email gönderimi için gerekli bilgileri kontrol et
        if not settings.DEFAULT_FROM_EMAIL:
            logger.warning("DEFAULT_FROM_EMAIL ayarlanmamış, email gönderilemiyor")
            return
        
        # Randevu bilgileri
        appointment_date = time_slot.start_time.strftime('%d %B %Y')
        appointment_time = time_slot.start_time.strftime('%H:%M')
        appointment_datetime = time_slot.start_time.strftime('%d %B %Y, %H:%M')
        
        # Hasta adını düzgün şekilde birleştir
        patient_name_parts = []
        if patient.first_name:
            patient_name_parts.append(patient.first_name)
        if patient.last_name:
            patient_name_parts.append(patient.last_name)
        patient_name = ' '.join(patient_name_parts) if patient_name_parts else patient.email
        
        # Hasta email'i
        patient_context = {
            'patient_name': patient_name,
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
            'patient_name': patient_name,
            'patient_email': patient.email,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'appointment_datetime': appointment_datetime,
            'notes': appointment.notes or 'Not bırakılmadı',
        }
        
        psychologist_subject = f'Yeni Randevu - {patient_name} - {appointment_datetime}'
        psychologist_message = render_to_string('emails/appointment_created_psychologist.txt', psychologist_context)
        psychologist_html_message = render_to_string('emails/appointment_created_psychologist.html', psychologist_context)
        
        # Email'leri asenkron olarak gönder (threading ile)
        # Böylece web sayfası yavaşlamaz ve timeout olmaz
        if patient.email:
            thread = threading.Thread(
                target=_send_email_sync,
                args=(patient_subject, patient_message, settings.DEFAULT_FROM_EMAIL, [patient.email], patient_html_message),
                daemon=True
            )
            thread.start()
            logger.info(f"Randevu oluşturma email'i gönderiliyor (Hasta): {patient.email}")
        
        if psychologist.email:
            thread = threading.Thread(
                target=_send_email_sync,
                args=(psychologist_subject, psychologist_message, settings.DEFAULT_FROM_EMAIL, [psychologist.email], psychologist_html_message),
                daemon=True
            )
            thread.start()
            logger.info(f"Randevu oluşturma email'i gönderiliyor (Psikolog): {psychologist.email}")
            
    except Exception as e:
        logger.error(f"Randevu oluşturma email'i gönderilirken hata: {str(e)}", exc_info=True)


def send_appointment_cancelled_email(appointment, cancelled_by_admin=False):
    """
    Randevu iptal edildiğinde hasta ve psikologa email gönder (asenkron)
    """
    try:
        patient = appointment.patient
        psychologist = appointment.time_slot.psychologist
        time_slot = appointment.time_slot
        
        # Email gönderimi için gerekli bilgileri kontrol et
        if not settings.DEFAULT_FROM_EMAIL:
            logger.warning("DEFAULT_FROM_EMAIL ayarlanmamış, email gönderilemiyor")
            return
        
        # Randevu bilgileri
        appointment_datetime = time_slot.start_time.strftime('%d %B %Y, %H:%M')
        
        # Hasta adını düzgün şekilde birleştir
        patient_name_parts = []
        if patient.first_name:
            patient_name_parts.append(patient.first_name)
        if patient.last_name:
            patient_name_parts.append(patient.last_name)
        patient_name = ' '.join(patient_name_parts) if patient_name_parts else patient.email
        
        # Hasta email'i
        patient_context = {
            'patient_name': patient_name,
            'appointment_datetime': appointment_datetime,
            'cancelled_by_admin': cancelled_by_admin,
        }
        
        patient_subject = f'Randevu İptali - {appointment_datetime}'
        patient_message = render_to_string('emails/appointment_cancelled_patient.txt', patient_context)
        patient_html_message = render_to_string('emails/appointment_cancelled_patient.html', patient_context)
        
        # Psikolog email'i
        psychologist_context = {
            'psychologist_name': psychologist.first_name or psychologist.email,
            'patient_name': patient_name,
            'appointment_datetime': appointment_datetime,
            'cancelled_by_admin': cancelled_by_admin,
        }
        
        psychologist_subject = f'Randevu İptal Edildi - {patient_name} - {appointment_datetime}'
        psychologist_message = render_to_string('emails/appointment_cancelled_psychologist.txt', psychologist_context)
        psychologist_html_message = render_to_string('emails/appointment_cancelled_psychologist.html', psychologist_context)
        
        # Email'leri asenkron olarak gönder (threading ile)
        if patient.email:
            thread = threading.Thread(
                target=_send_email_sync,
                args=(patient_subject, patient_message, settings.DEFAULT_FROM_EMAIL, [patient.email], patient_html_message),
                daemon=True
            )
            thread.start()
            logger.info(f"Randevu iptal email'i gönderiliyor (Hasta): {patient.email}")
        
        if psychologist.email:
            thread = threading.Thread(
                target=_send_email_sync,
                args=(psychologist_subject, psychologist_message, settings.DEFAULT_FROM_EMAIL, [psychologist.email], psychologist_html_message),
                daemon=True
            )
            thread.start()
            logger.info(f"Randevu iptal email'i gönderiliyor (Psikolog): {psychologist.email}")
            
    except Exception as e:
        logger.error(f"Randevu iptal email'i gönderilirken hata: {str(e)}", exc_info=True)