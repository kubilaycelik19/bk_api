"""
SendGrid Email Backend - Django email gönderimi için custom backend
Render'da SMTP portu bloklu olduğu için SendGrid API kullanıyoruz
"""
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)


class SendGridBackend(BaseEmailBackend):
    """
    SendGrid API kullanarak email gönderen Django email backend
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        
        if not self.api_key:
            logger.warning("⚠️ SENDGRID_API_KEY ayarlanmamış, email gönderilemeyecek")
            self.sendgrid_client = None
        else:
            try:
                self.sendgrid_client = SendGridAPIClient(api_key=self.api_key)
                logger.info("✅ SendGrid client başarıyla oluşturuldu")
            except Exception as e:
                logger.error(f"❌ SendGrid client oluşturulamadı: {str(e)}", exc_info=True)
                self.sendgrid_client = None
    
    def send_messages(self, email_messages):
        """
        Django email mesajlarını SendGrid API üzerinden gönderir
        """
        if not self.sendgrid_client:
            if not self.fail_silently:
                raise Exception("SendGrid API key ayarlanmamış")
            return 0
        
        sent_count = 0
        
        for email_message in email_messages:
            try:
                # Django EmailMessage objesinden bilgileri al
                from_email = email_message.from_email or self.from_email
                to_emails = email_message.to
                subject = email_message.subject
                
                # Plain text ve HTML content
                body_text = email_message.body
                body_html = None
                
                # HTML alternatif var mı?
                if hasattr(email_message, 'alternatives') and email_message.alternatives:
                    for content, mimetype in email_message.alternatives:
                        if mimetype == 'text/html':
                            body_html = content
                            break
                
                # Eğer html_message parametresi varsa onu kullan
                if hasattr(email_message, 'html_message') and email_message.html_message:
                    body_html = email_message.html_message
                
                # SendGrid Mail objesi oluştur
                message = Mail(
                    from_email=Email(from_email),
                    to_emails=[To(email) for email in to_emails],
                    subject=subject,
                    plain_text_content=Content("text/plain", body_text) if body_text else None,
                    html_content=Content("text/html", body_html) if body_html else None,
                )
                
                # Email'i gönder
                response = self.sendgrid_client.send(message)
                
                # Başarı kontrolü (2xx status code)
                if 200 <= response.status_code < 300:
                    logger.info(f"✅ Email başarıyla gönderildi: {to_emails}")
                    sent_count += 1
                else:
                    error_msg = f"SendGrid API hatası: {response.status_code} - {response.body}"
                    logger.error(f"❌ {error_msg}")
                    if not self.fail_silently:
                        raise Exception(error_msg)
                        
            except Exception as e:
                logger.error(f"❌ Email gönderilirken hata: {str(e)}", exc_info=True)
                if not self.fail_silently:
                    raise
        
        return sent_count

