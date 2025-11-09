# SendGrid Kurulum Rehberi

SendGrid, Render.com free tier'da çalışan ücretsiz bir email servisidir. Gmail SMTP yerine SendGrid kullanarak email gönderebilirsiniz.

## Adım 1: SendGrid'a Kaydolun

1. **SendGrid'a gidin**
   - https://sendgrid.com adresine gidin
   - "Start for free" butonuna tıklayın

2. **Hesap oluşturun**
   - Email adresinizi girin
   - Şifrenizi oluşturun
   - Hesabınızı doğrulayın

## Adım 2: Single Sender Verification

1. **Dashboard'a gidin**
   - SendGrid Dashboard → Settings → Sender Authentication
   - "Single Sender Verification" seçeneğine tıklayın

2. **Sender oluşturun**
   - "Create a Sender" butonuna tıklayın
   - Email adresinizi girin (örn: `noreply@yourdomain.com`)
   - Ad, şirket, adres bilgilerinizi girin
   - Email adresinizi doğrulayın (SendGrid'e gönderilen doğrulama email'ini açın)

**Not**: Eğer domain'iniz yoksa, Gmail adresinizi kullanabilirsiniz (örn: `yourname@gmail.com`)

## Adım 3: API Key Oluşturun

1. **API Keys sayfasına gidin**
   - SendGrid Dashboard → Settings → API Keys
   - "Create API Key" butonuna tıklayın

2. **API Key oluşturun**
   - **Name**: `Django API Key` (veya istediğiniz bir isim)
   - **API Key Permissions**: "Full Access" seçin (veya sadece "Mail Send" seçebilirsiniz)
   - "Create & View" butonuna tıklayın

3. **API Key'i kopyalayın**
   - ⚠️ **ÖNEMLİ**: API key'i bir kez gösterilir, kopyalayın ve güvenli bir yere kaydedin
   - API key şu formatta olacak: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Adım 4: Render.com Environment Variables

1. **Render.com Dashboard'a gidin**
   - https://dashboard.render.com
   - Servisinizi seçin
   - "Environment" sekmesine gidin

2. **Environment Variables ekleyin**
   Aşağıdaki environment variable'ları ekleyin:

   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=<SENDGRID_API_KEY>
   DEFAULT_FROM_EMAIL=<VERIFIED_EMAIL_ADDRESS>
   ```

   **Örnek:**
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

   **Notlar:**
   - `EMAIL_HOST_USER` her zaman `apikey` olmalı (değiştirmeyin)
   - `EMAIL_HOST_PASSWORD` SendGrid API key'iniz olmalı
   - `DEFAULT_FROM_EMAIL` SendGrid'de verify ettiğiniz email adresi olmalı

## Adım 5: Deploy'u Yeniden Yapın

1. **Render.com Dashboard'a gidin**
   - Servisinizi seçin
   - "Manual Deploy" → "Deploy latest commit" butonuna tıklayın
   - Deploy'u bekleyin

## Adım 6: Test Edin

1. **Frontend'den randevu oluşturun**
   - Frontend'den yeni bir randevu oluşturun
   - Email'lerin gönderildiğini kontrol edin

2. **Log'ları kontrol edin**
   - Render.com Dashboard → Logs
   - Şu log'u görmelisiniz:
   ```
   ✅ Email başarıyla gönderildi: ['recipient@example.com']
   ```

## Troubleshooting

### Sorun 1: "Email gönderilemedi" hatası

**Çözüm:**
- SendGrid API key'inizi kontrol edin
- `EMAIL_HOST_USER=apikey` olduğundan emin olun (değiştirmeyin)
- `DEFAULT_FROM_EMAIL` SendGrid'de verify edilmiş bir email olmalı
- SendGrid Dashboard → Activity → Email Activity'de email'lerin durumunu kontrol edin

### Sorun 2: "Sender not verified" hatası

**Çözüm:**
- SendGrid Dashboard → Settings → Sender Authentication
- Single Sender Verification'da email adresinizi verify edin
- Email adresinize gönderilen doğrulama email'ini açın ve link'e tıklayın

### Sorun 3: Email'ler spam klasörüne düşüyor

**Çözüm:**
- SendGrid Dashboard → Settings → Sender Authentication
- Domain Authentication yapın (domain'iniz varsa)
- Veya Single Sender Verification kullanın (domain'iniz yoksa)

## SendGrid Free Tier Limitleri

- **100 email/gün** (ücretsiz)
- **Unlimited contacts**
- **Email API access**
- **SMTP relay**

Küçük projeler için yeterlidir. Daha fazla email göndermek isterseniz ücretli plana geçebilirsiniz.

## Kaynaklar

- SendGrid Documentation: https://docs.sendgrid.com
- SendGrid SMTP Settings: https://docs.sendgrid.com/for-developers/sending-email/getting-started-smtp
- SendGrid API Keys: https://docs.sendgrid.com/ui/account-and-settings/api-keys

## Sonuç

SendGrid kurulumu tamamlandı! Artık Render.com free tier'da email gönderebilirsiniz.

**Önemli:**
- API key'inizi güvenli tutun
- Email adresinizi verify edin
- Free tier limitlerini aşmamaya dikkat edin (100 email/gün)

