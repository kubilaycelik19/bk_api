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
    Randevu oluşturulduğunda hasta ve psikologa email gönder
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
        
        # Email gönder
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
            
    except Exception as e:
        logger.error(f"Randevu oluşturma email'i gönderilirken hata: {str(e)}", exc_info=True)


def send_appointment_cancelled_email(appointment, cancelled_by_admin=False):
    """
    Randevu iptal edildiğinde hasta ve psikologa email gönder
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
        
        # Email gönder
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

