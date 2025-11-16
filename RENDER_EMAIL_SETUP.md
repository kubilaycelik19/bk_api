# Render'da Email Gönderimi Sorun Giderme

## ❌ Problem: "Network is unreachable" Hatası

Render'da email gönderilirken `[Errno 101] Network is unreachable` hatası alınıyorsa, bu genellikle SMTP port kısıtlamalarından kaynaklanır.

## 🔧 Çözüm 1: Port 465 (SSL) Kullanın

Render'da bazı durumlarda port 587 (TLS) bloklanabilir, ancak port 465 (SSL) çalışabilir.

### Render'da Environment Variable'ları Güncelleyin:

1. **Render Dashboard'a gidin**: https://dashboard.render.com
2. **Backend servisinizi seçin** (bk-api)
3. **Environment** sekmesine gidin
4. **Şu environment variable'ları ekleyin/güncelleyin:**

   **Email Host:**
   - **Key**: `EMAIL_HOST`
   - **Value**: `smtp.gmail.com`

   **Email Port (SSL için):**
   - **Key**: `EMAIL_PORT`
   - **Value**: `465`

   **Email SSL (ÖNEMLİ):**
   - **Key**: `EMAIL_USE_SSL`
   - **Value**: `True`

   **Email TLS (Port 465'te kapatın):**
   - **Key**: `EMAIL_USE_TLS`
   - **Value**: `False`

   **Email User:**
   - **Key**: `EMAIL_HOST_USER`
   - **Value**: `pskbasakseref@gmail.com` (Gmail adresiniz)

   **Email Password (Gmail App Password - 16 haneli):**
   - **Key**: `EMAIL_HOST_PASSWORD`
   - **Value**: `xxxx xxxx xxxx xxxx` (16 haneli App Password - **Normal şifre değil!**)

5. **Servisi yeniden deploy edin**

### ⚠️ Gmail App Password Nasıl Alınır?

1. Google Hesabınıza gidin: https://myaccount.google.com
2. **Güvenlik** → **2 Adımlı Doğrulama** (açık olmalı)
3. **Uygulama şifreleri** bölümüne gidin
4. **Uygulama seçin**: "Mail"
5. **Cihaz seçin**: "Diğer (Özel ad)" → "Render" yazın
6. **Oluştur** butonuna tıklayın
7. **16 haneli şifreyi kopyalayın** (örnek: `abcd efgh ijkl mnop`)
8. Boşlukları kaldırarak Render'a ekleyin: `abcdefghijklmnop`

## 🔧 Çözüm 2: Port 587 (TLS) Deneyin (SSL Çalışmazsa)

Eğer port 465 çalışmazsa, port 587'i deneyin:

- `EMAIL_PORT`: `587`
- `EMAIL_USE_TLS`: `True`
- `EMAIL_USE_SSL`: `False`

## 🔧 Çözüm 3: SendGrid veya Mailgun Kullanın

Render'da SMTP sorunları devam ederse, üçüncü parti email servisleri kullanabilirsiniz:

### SendGrid (Önerilen):
- Ücretsiz tier: 100 email/gün
- Render ile iyi entegrasyon
- Django için: `django-sendgrid-v5` paketi

### Mailgun:
- Ücretsiz tier: 5,000 email/ay (ilk 3 ay)
- SMTP ve API desteği

## 📋 Kontrol Listesi

- [ ] Gmail App Password kullanıyorum (normal şifre değil)
- [ ] Port 465 veya 587 denedim
- [ ] SSL/TLS ayarları doğru
- [ ] Environment variable'ları Render'da ekledim
- [ ] Servisi yeniden deploy ettim
- [ ] Log'larda hata var mı kontrol ettim

## 🧪 Test

Environment variable'ları güncelledikten ve redeploy yaptıktan sonra:
1. Yeni bir randevu oluşturun
2. Render log'larını kontrol edin
3. Email'lerin gittiğini doğrulayın

## 📝 Notlar

- **Randevu oluşturuluyor ama email gönderilemiyor**: Bu normal, email hatası randevu oluşturmayı engellemez (fail_silently=False olsa bile threading kullanıldığı için ana thread etkilenmez)
- **Threading kullanılıyor**: Email gönderimi asenkron yapılıyor, web isteği yavaşlamıyor
- **Retry mekanizması yok**: Şu an için email başarısız olursa tekrar denenmiyor (ileride eklenebilir)

