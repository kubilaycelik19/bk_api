"""
Email gönderme servisi - Randevu bildirimleri için
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def send_appointment_created_email(appointment):
    """
    Randevu oluşturulduğunda hasta ve boss email adresine email gönder
    - Hasta: Randevu onayı alır
    - Boss: Yeni randevu bildirimi alır
    """
    try:
        patient = appointment.patient
        psychologist = appointment.time_slot.psychologist
        time_slot = appointment.time_slot
        boss_email = settings.BOSS_EMAIL
        
        # Randevu bilgileri
        appointment_date = time_slot.start_time.strftime('%d %B %Y')
        appointment_time = time_slot.start_time.strftime('%H:%M')
        appointment_datetime = time_slot.start_time.strftime('%d %B %Y, %H:%M')
        
        # Hasta email'i - Randevu onayı
        patient_name = patient.first_name + ' ' + patient.last_name if (patient.first_name or patient.last_name) else patient.email
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
        
        # Boss email'i - Yeni randevu bildirimi
        boss_context = {
            'psychologist_name': 'Yönetici',  # Boss için genel bir isim
            'patient_name': patient_name,
            'patient_email': patient.email,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'appointment_datetime': appointment_datetime,
            'notes': appointment.notes or 'Not bırakılmadı',
        }
        
        boss_subject = f'Yeni Randevu - {patient_name} - {appointment_datetime}'
        boss_message = render_to_string('emails/appointment_created_psychologist.txt', boss_context)
        boss_html_message = render_to_string('emails/appointment_created_psychologist.html', boss_context)
        
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
        
        # Email gönder - Boss
        if boss_email:
            send_mail(
                subject=boss_subject,
                message=boss_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[boss_email],
                html_message=boss_html_message,
                fail_silently=False,
            )
            logger.info(f"Randevu oluşturma email'i gönderildi (Boss): {boss_email}")
            
    except Exception as e:
        logger.error(f"Randevu oluşturma email'i gönderilirken hata: {str(e)}", exc_info=True)


def send_appointment_cancelled_email(appointment, cancelled_by_admin=False):
    """
    Randevu iptal edildiğinde hasta ve boss email adresine email gönder
    - Hasta: Randevu iptali bildirimi alır
    - Boss: Randevu iptali bildirimi alır
    """
    try:
        patient = appointment.patient
        psychologist = appointment.time_slot.psychologist if appointment.time_slot else None
        time_slot = appointment.time_slot
        boss_email = settings.BOSS_EMAIL
        
        # Randevu bilgileri
        appointment_datetime = time_slot.start_time.strftime('%d %B %Y, %H:%M') if time_slot else 'Bilinmeyen Tarih'
        
        # Hasta email'i
        patient_name = patient.first_name + ' ' + patient.last_name if (patient.first_name or patient.last_name) else patient.email
        patient_context = {
            'patient_name': patient_name,
            'appointment_datetime': appointment_datetime,
            'cancelled_by_admin': cancelled_by_admin,
        }
        
        patient_subject = f'Randevu İptali - {appointment_datetime}'
        patient_message = render_to_string('emails/appointment_cancelled_patient.txt', patient_context)
        patient_html_message = render_to_string('emails/appointment_cancelled_patient.html', patient_context)
        
        # Boss email'i
        boss_context = {
            'psychologist_name': 'Yönetici',  # Boss için genel bir isim
            'patient_name': patient_name,
            'appointment_datetime': appointment_datetime,
            'cancelled_by_admin': cancelled_by_admin,
        }
        
        boss_subject = f'Randevu İptal Edildi - {patient_name} - {appointment_datetime}'
        boss_message = render_to_string('emails/appointment_cancelled_psychologist.txt', boss_context)
        boss_html_message = render_to_string('emails/appointment_cancelled_psychologist.html', boss_context)
        
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
        
        # Email gönder - Boss
        if boss_email:
            send_mail(
                subject=boss_subject,
                message=boss_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[boss_email],
                html_message=boss_html_message,
                fail_silently=False,
            )
            logger.info(f"Randevu iptal email'i gönderildi (Boss): {boss_email}")
            
    except Exception as e:
        logger.error(f"Randevu iptal email'i gönderilirken hata: {str(e)}", exc_info=True)

