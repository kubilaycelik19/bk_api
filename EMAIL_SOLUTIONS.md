# Render.com Email Gönderme Sorunu - Çözümler

## Sorun

Render.com free tier'da outbound SMTP bağlantıları engellenmiş olabilir. Bu durumda Gmail SMTP'ye (`smtp.gmail.com:587`) bağlanamazsınız ve şu hatayı alırsınız:

```
OSError: [Errno 101] Network is unreachable
```

## ⚠️ ÖNEMLİ: Email Gönderme Kritikse

Eğer email göndermek sizin için kritikse, **HOSTING_EMAIL_OPTIONS.md** dosyasına bakın. Orada şu seçenekleri bulacaksınız:

1. **Render.com Ücretli Plan** - Gmail SMTP direkt çalışır ($7/ay, migration yok)
2. **Google Cloud Platform (GCP) Free Tier** - Gmail SMTP çalışır (ücretsiz, migration gerekiyor)
3. **AWS Free Tier** - AWS SES çalışır (62,000 email/ay ücretsiz, migration gerekiyor)
4. **Railway.app Free Tier** - Gmail SMTP çalışır (ücretsiz, migration gerekiyor)
5. **SendGrid/Mailgun** - Render free tier'da çalışır (ücretsiz, migration yok) ⭐ EN KOLAY

## Çözümler

### 1. SendGrid (Önerilen - Ücretsiz)

SendGrid, ücretsiz planında ayda 100 email gönderme hakkı verir.

#### Kurulum:

1. **SendGrid'a kaydolun**
   - https://sendgrid.com adresine gidin
   - Ücretsiz hesap oluşturun

2. **API Key Oluşturun**
   - Dashboard → Settings → API Keys
   - "Create API Key" butonuna tıklayın
   - API key'i kopyalayın

3. **Render.com Environment Variables**
   - `EMAIL_BACKEND`: `django.core.mail.backends.smtp.EmailBackend`
   - `EMAIL_HOST`: `smtp.sendgrid.net`
   - `EMAIL_PORT`: `587`
   - `EMAIL_USE_TLS`: `True`
   - `EMAIL_HOST_USER`: `apikey` (değiştirmeyin)
   - `EMAIL_HOST_PASSWORD`: SendGrid API key'iniz
   - `DEFAULT_FROM_EMAIL`: Gönderen email adresi (SendGrid'de verify edilmiş)

#### Django Settings:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

### 2. Mailgun (Ücretsiz)

Mailgun, ücretsiz planında ayda 5,000 email gönderme hakkı verir.

#### Kurulum:

1. **Mailgun'a kaydolun**
   - https://mailgun.com adresine gidin
   - Ücretsiz hesap oluşturun

2. **Domain Verify Edin**
   - Dashboard → Sending → Domains
   - Domain'inizi verify edin

3. **SMTP Credentials**
   - Dashboard → Sending → Domain Settings → SMTP credentials
   - SMTP username ve password'u kopyalayın

4. **Render.com Environment Variables**
   - `EMAIL_HOST`: `smtp.mailgun.org`
   - `EMAIL_PORT`: `587`
   - `EMAIL_USE_TLS`: `True`
   - `EMAIL_HOST_USER`: Mailgun SMTP username
   - `EMAIL_HOST_PASSWORD`: Mailgun SMTP password
   - `DEFAULT_FROM_EMAIL`: Verify edilmiş domain'den email

### 3. AWS SES (Amazon Simple Email Service)

AWS SES, ücretsiz tier'da ayda 62,000 email gönderme hakkı verir (sadece EC2'den).

#### Kurulum:

1. **AWS SES'i aktifleştirin**
   - AWS Console → SES
   - Email address'i verify edin
   - Sandbox modundan çıkın (production için)

2. **SMTP Credentials**
   - AWS Console → SES → SMTP Settings
   - "Create SMTP credentials" butonuna tıklayın
   - SMTP username ve password'u kopyalayın

3. **Render.com Environment Variables**
   - `EMAIL_HOST`: `email-smtp.{region}.amazonaws.com` (örn: `email-smtp.us-east-1.amazonaws.com`)
   - `EMAIL_PORT`: `587`
   - `EMAIL_USE_TLS`: `True`
   - `EMAIL_HOST_USER`: AWS SES SMTP username
   - `EMAIL_HOST_PASSWORD`: AWS SES SMTP password
   - `DEFAULT_FROM_EMAIL`: Verify edilmiş email adresi

### 4. Email Göndermeyi Devre Dışı Bırakma (Geçici)

Eğer email göndermeye ihtiyacınız yoksa, geçici olarak devre dışı bırakabilirsiniz:

#### Render.com Environment Variable:
- `EMAIL_ENABLED`: `False`

Bu durumda email gönderme fonksiyonları çalışmaz ama uygulama normal çalışmaya devam eder.

## Test

Email servisini test etmek için:

```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email.',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)
```

## Notlar

- Render.com free tier'da outbound SMTP bağlantıları engellenmiş olabilir
- SendGrid ve Mailgun gibi servisler bu sorunu çözer
- Ücretsiz planlar genellikle yeterlidir (küçük projeler için)
- Production'da email göndermeyi mutlaka test edin

## Öneri

**SendGrid** kullanmanızı öneririm çünkü:
- ✅ Ücretsiz plan yeterli (ayda 100 email)
- ✅ Kolay kurulum
- ✅ Render.com'da çalışır
- ✅ İyi dokümantasyon
- ✅ Güvenilir servis

## Kaynaklar

- SendGrid: https://sendgrid.com
- Mailgun: https://mailgun.com
- AWS SES: https://aws.amazon.com/ses/
- Django Email: https://docs.djangoproject.com/en/stable/topics/email/

