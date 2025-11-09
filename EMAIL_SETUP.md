# 📧 Email Kurulum Rehberi

Bu rehber, Gmail SMTP ile email gönderme özelliğini aktif etmek için gereken adımları içerir.

## 🔐 Gmail Uygulama Şifresi Oluşturma

### Adım 1: Google Hesabınızda 2 Adımlı Doğrulamayı Aktif Edin

1. [Google Hesap Güvenliği](https://myaccount.google.com/security) sayfasına gidin
2. "2 Adımlı Doğrulama" bölümünü bulun
3. Eğer aktif değilse, "Başlat" butonuna tıklayın ve adımları tamamlayın

### Adım 2: Uygulama Şifresi Oluşturun

1. [Uygulama Şifreleri](https://myaccount.google.com/apppasswords) sayfasına gidin
2. "Uygulama seçin" dropdown'ından "Posta" seçin
3. "Cihaz seçin" dropdown'ından "Diğer (Özel ad)" seçin
4. "Diğer" yazın ve "Oluştur" butonuna tıklayın
5. **16 haneli şifreyi kopyalayın** (boşluksuz, örnek: `abcd efgh ijkl mnop`)

### Adım 3: .env Dosyasını Yapılandırın

`bk_api` klasöründe `.env` dosyası oluşturun veya mevcut dosyayı düzenleyin:

```env
# Email Ayarları
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

**Önemli Notlar:**
- `EMAIL_HOST_USER`: Gmail adresiniz (tam adres)
- `EMAIL_HOST_PASSWORD`: 16 haneli uygulama şifreniz (boşluksuz)
- Normal Gmail şifrenizi **ASLA** kullanmayın, sadece uygulama şifresi kullanın

## ✅ Test Etme

### 1. API'yi Başlatın

```powershell
cd bk_api
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

### 2. Yeni Bir Randevu Oluşturun

Postman veya frontend'den yeni bir randevu oluşturun. Email'ler otomatik olarak gönderilecektir.

### 3. Email'leri Kontrol Edin

- **Hasta email'i**: Randevu alan kullanıcının email adresine gönderilir
- **Psikolog email'i**: Slot'u oluşturan psikologun (superuser) email adresine gönderilir

## 🔍 Sorun Giderme

### ❌ "Authentication failed" Hatası

**Çözüm:**
- Uygulama şifresini doğru kopyaladığınızdan emin olun (boşluksuz)
- 2 Adımlı Doğrulamanın aktif olduğundan emin olun
- `.env` dosyasındaki `EMAIL_HOST_USER` ve `EMAIL_HOST_PASSWORD` değerlerini kontrol edin

### ❌ Email Gönderilmiyor

**Çözüm:**
- Django loglarını kontrol edin: `python manage.py runserver` çıktısına bakın
- `.env` dosyasının `bk_api` klasöründe olduğundan emin olun
- API'yi yeniden başlatın (`.env` değişiklikleri için gerekli)

### ❌ "Less secure app access" Hatası

**Çözüm:**
- Gmail artık "Daha az güvenli uygulama erişimi"ni desteklemiyor
- **Mutlaka uygulama şifresi kullanın** (yukarıdaki adımları takip edin)

## 📝 Email Özellikleri

- ✅ **Asenkron gönderim**: Email gönderimi web sayfasını yavaşlatmaz
- ✅ **HTML format**: Güzel formatlanmış email'ler
- ✅ **Otomatik bildirim**: Randevu oluşturulduğunda ve iptal edildiğinde otomatik email gönderilir
- ✅ **Çift bildirim**: Hem hasta hem psikolog email alır

## 🚀 Canlı Ortam (Production)

Render.com veya başka bir hosting servisi kullanıyorsanız:

1. Environment Variables'a şu değişkenleri ekleyin:
   - `EMAIL_HOST_USER`
   - `EMAIL_HOST_PASSWORD`
   - `EMAIL_HOST` (varsayılan: `smtp.gmail.com`)
   - `EMAIL_PORT` (varsayılan: `587`)
   - `EMAIL_USE_TLS` (varsayılan: `True`)

2. `.env` dosyası kullanmıyorsanız, environment variables otomatik olarak kullanılacaktır.

