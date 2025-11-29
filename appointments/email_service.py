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
    Django database connection'larını thread-safe hale getirmek için close_all() kullanıyoruz
    """
    from django.db import connections
    try:
        # Thread'de Django database connection'larını kapat
        # Böylece yeni connection açılır ve thread-safe çalışır
        connections.close_all()
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"✅ Email başarıyla gönderildi: {recipient_list}")
    except Exception as e:
        logger.error(f"❌ Email gönderilirken hata: {str(e)}", exc_info=True)
    finally:
        # Thread sonunda connection'ları temizle
        connections.close_all()


def send_appointment_created_email(appointment):
    """
    Randevu oluşturulduğunda hasta ve psikologa email gönder (asenkron)
    """
    print(f"📧 [EMAIL SERVICE] send_appointment_created_email çağrıldı - Appointment ID: {appointment.id}")
    logger.info(f"📧 [EMAIL SERVICE] send_appointment_created_email çağrıldı - Appointment ID: {appointment.id}")
    
    try:
        patient = appointment.patient
        psychologist = appointment.time_slot.psychologist
        time_slot = appointment.time_slot
        print(f"📧 [EMAIL SERVICE] Randevu bilgileri alındı - Hasta: {patient.email}, Psikolog: {psychologist.email}")
        
        # Email gönderimi için gerekli bilgileri kontrol et
        if not settings.DEFAULT_FROM_EMAIL:
            warning_msg = "⚠️ DEFAULT_FROM_EMAIL ayarlanmamış, email gönderilemiyor (SendGrid için doğrulanmış email adresi gerekli)"
            print(f"⚠️ [EMAIL SERVICE] {warning_msg}")
            logger.warning(warning_msg)
            return
        
        if not getattr(settings, 'SENDGRID_API_KEY', None):
            warning_msg = "⚠️ SENDGRID_API_KEY ayarlanmamış, email gönderilemiyor"
            print(f"⚠️ [EMAIL SERVICE] {warning_msg}")
            logger.warning(warning_msg)
            return
        
        # Email ayarlarını logla (debug için)
        logger.info(f"📧 Email ayarları: FROM={settings.DEFAULT_FROM_EMAIL} (SendGrid)")
        
        # Türkçe ay isimleri mapping'i
        turkish_months = {
            'January': 'Ocak', 'February': 'Şubat', 'March': 'Mart',
            'April': 'Nisan', 'May': 'Mayıs', 'June': 'Haziran',
            'July': 'Temmuz', 'August': 'Ağustos', 'September': 'Eylül',
            'October': 'Ekim', 'November': 'Kasım', 'December': 'Aralık'
        }
        
        def format_turkish_date(dt):
            """Tarihi Türkçe formatında döndürür: gün ay yıl, saat:dakika"""
            date_str = dt.strftime('%d %B %Y')
            time_str = dt.strftime('%H:%M')
            # İngilizce ay ismini Türkçe'ye çevir
            for en_month, tr_month in turkish_months.items():
                date_str = date_str.replace(en_month, tr_month)
            return date_str, time_str
        
        # Randevu bilgileri
        appointment_date, appointment_time = format_turkish_date(time_slot.start_time)
        appointment_datetime = f"{appointment_date}, {appointment_time}"
        
        # Ödeme tarihi (randevudan 24 saat önce)
        payment_deadline = time_slot.start_time - timedelta(hours=24)
        payment_deadline_date, payment_deadline_time = format_turkish_date(payment_deadline)
        payment_deadline_datetime = f"{payment_deadline_date}, {payment_deadline_time}"
        
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
            'payment_deadline_date': payment_deadline_date,
            'payment_deadline_time': payment_deadline_time,
            'payment_deadline_datetime': payment_deadline_datetime,
            'notes': appointment.notes or 'Not bırakılmadı',
            'psychologist_name': psychologist.first_name or psychologist.email,
        }
        
        patient_subject = f'Randevu Onayı - {appointment_datetime}'
        try:
            patient_message = render_to_string('emails/appointment_created_patient.txt', patient_context)
            patient_html_message = render_to_string('emails/appointment_created_patient.html', patient_context)
        except Exception as e:
            logger.error(f"Email template render hatası (Hasta): {str(e)}", exc_info=True)
            return
        
        # Psikolog email'i
        psychologist_context = {
            'psychologist_name': psychologist.first_name or psychologist.email,
            'patient_name': patient_name,
            'patient_email': patient.email,
            'patient_phone': patient.phone_number or 'Belirtilmemiş',
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'appointment_datetime': appointment_datetime,
            'payment_deadline_date': payment_deadline_date,
            'payment_deadline_time': payment_deadline_time,
            'payment_deadline_datetime': payment_deadline_datetime,
            'notes': appointment.notes or 'Not bırakılmadı',
        }
        
        psychologist_subject = f'Yeni Randevu - {patient_name} - {appointment_datetime}'
        psychologist_message = render_to_string('emails/appointment_created_psychologist.txt', psychologist_context)
        psychologist_html_message = render_to_string('emails/appointment_created_psychologist.html', psychologist_context)
        
        # Email'leri asenkron olarak gönder (threading ile)
        # Böylece web sayfası yavaşlamaz ve timeout olmaz
        # Production'da thread'lerin çalışması için daemon=False kullanıyoruz
        if patient.email:
            logger.info(f"📧 Hasta email'i hazırlanıyor: {patient.email}")
            try:
                thread = threading.Thread(
                    target=_send_email_sync,
                    args=(patient_subject, patient_message, settings.DEFAULT_FROM_EMAIL, [patient.email], patient_html_message),
                    daemon=False,  # daemon=False: Thread ana process'ten bağımsız çalışır
                    name=f"EmailThread-Patient-{appointment.id}"
                )
                thread.start()
                logger.info(f"✅ Thread başlatıldı: Hasta email'i gönderiliyor - {patient.email}")
            except Exception as e:
                logger.error(f"❌ Thread başlatılamadı (Hasta): {str(e)}", exc_info=True)
        
        if psychologist.email:
            logger.info(f"📧 Psikolog email'i hazırlanıyor: {psychologist.email}")
            try:
                thread = threading.Thread(
                    target=_send_email_sync,
                    args=(psychologist_subject, psychologist_message, settings.DEFAULT_FROM_EMAIL, [psychologist.email], psychologist_html_message),
                    daemon=False,  # daemon=False: Thread ana process'ten bağımsız çalışır
                    name=f"EmailThread-Psychologist-{appointment.id}"
                )
                thread.start()
                logger.info(f"✅ Thread başlatıldı: Psikolog email'i gönderiliyor - {psychologist.email}")
            except Exception as e:
                logger.error(f"❌ Thread başlatılamadı (Psikolog): {str(e)}", exc_info=True)
            
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
            logger.warning("⚠️ DEFAULT_FROM_EMAIL ayarlanmamış, email gönderilemiyor (SendGrid için doğrulanmış email adresi gerekli)")
            return
        
        if not getattr(settings, 'SENDGRID_API_KEY', None):
            logger.warning("⚠️ SENDGRID_API_KEY ayarlanmamış, email gönderilemiyor")
            return
        
        # Email ayarlarını logla (debug için)
        logger.info(f"📧 Email ayarları: FROM={settings.DEFAULT_FROM_EMAIL} (SendGrid)")
        
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
            logger.info(f"📧 Hasta iptal email'i hazırlanıyor: {patient.email}")
            try:
                thread = threading.Thread(
                    target=_send_email_sync,
                    args=(patient_subject, patient_message, settings.DEFAULT_FROM_EMAIL, [patient.email], patient_html_message),
                    daemon=False,  # daemon=False: Thread ana process'ten bağımsız çalışır
                    name=f"EmailThread-Cancel-Patient-{appointment.id}"
                )
                thread.start()
                logger.info(f"✅ Thread başlatıldı: Hasta iptal email'i gönderiliyor - {patient.email}")
            except Exception as e:
                logger.error(f"❌ Thread başlatılamadı (Hasta İptal): {str(e)}", exc_info=True)
        
        if psychologist.email:
            logger.info(f"📧 Psikolog iptal email'i hazırlanıyor: {psychologist.email}")
            try:
                thread = threading.Thread(
                    target=_send_email_sync,
                    args=(psychologist_subject, psychologist_message, settings.DEFAULT_FROM_EMAIL, [psychologist.email], psychologist_html_message),
                    daemon=False,  # daemon=False: Thread ana process'ten bağımsız çalışır
                    name=f"EmailThread-Cancel-Psychologist-{appointment.id}"
                )
                thread.start()
                logger.info(f"✅ Thread başlatıldı: Psikolog iptal email'i gönderiliyor - {psychologist.email}")
            except Exception as e:
                logger.error(f"❌ Thread başlatılamadı (Psikolog İptal): {str(e)}", exc_info=True)
            
    except Exception as e:
        logger.error(f"Randevu iptal email'i gönderilirken hata: {str(e)}", exc_info=True)