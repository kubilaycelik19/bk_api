# SendGrid Kurulum Rehberi

## 📧 SendGrid Nedir?

SendGrid, Render'da SMTP portu bloklu olduğu için kullandığımız profesyonel email gönderme servisidir.
- ✅ Ücretsiz plan: **100 email/gün**
- ✅ Render'da çalışır (API kullanır, SMTP portu gerekmez)
- ✅ Güvenilir ve hızlı email gönderimi

---

## 🚀 Adım Adım Kurulum

### 1. SendGrid Hesabı Oluşturun

1. **SendGrid'e kaydolun**: https://signup.sendgrid.com/
   - Email adresinizle ücretsiz hesap oluşturun
   - Telefon numarası doğrulaması istenebilir

2. **Email doğrulama**: Kayıt sonrası email'inizi doğrulayın

---

### 2. API Key Oluşturun

1. **SendGrid Dashboard'a girin**: https://app.sendgrid.com/

2. **Settings** → **API Keys** menüsüne gidin

3. **"Create API Key"** butonuna tıklayın

4. **API Key ayarları:**
   - **API Key Name**: `BK Project Production` (veya istediğiniz bir isim)
   - **API Key Permissions**: **"Full Access"** seçin (veya sadece **"Mail Send"** yeterli)
   
5. **"Create & View"** butonuna tıklayın

6. **⚠️ ÖNEMLİ: API Key'i kopyalayın!**
   - API Key sadece bir kez gösterilir
   - Güvenli bir yere kaydedin
   - Format: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 3. Sender Authentication (Email Doğrulama)

SendGrid'den email gönderebilmek için **gönderen email adresini** doğrulamanız gerekir.

#### Seçenek A: Single Sender Verification (Hızlı - Test için)

1. **Settings** → **Sender Authentication** → **Single Sender Verification**

2. **"Create a Sender"** butonuna tıklayın

3. **Formu doldurun:**
   - **From Email Address**: Göndereceğiniz email adresi (örn: `pskbasakseref@gmail.com`)
   - **From Name**: Görünecek isim (örn: `Başak Şeref`)
   - **Reply To**: Yanıt adresi (genelde aynı email)
   - **Company Address**: Adres bilgileri (gerekli)

4. **"Create"** butonuna tıklayın

5. **Email doğrulama**: SendGrid size bir doğrulama email'i gönderir
   - Email'inizi açın ve doğrulama linkine tıklayın
   - ✅ **Doğrulanmış email adresini not edin** (settings'de kullanacağız)

#### Seçenek B: Domain Authentication (Production için önerilir - İsteğe bağlı)

Kendi domain'iniz varsa (örn: `basakseref.com`), domain doğrulaması yapabilirsiniz. Bu daha profesyonel görünür ama zorunlu değildir.

---

### 4. Environment Variables Ayarlayın (Render'da)

1. **Render Dashboard'a gidin**: https://dashboard.render.com/

2. **API servisinizi seçin** (bk-api)

3. **Environment** sekmesine gidin

4. **Yeni environment variable'ları ekleyin:**

   **a) SendGrid API Key:**
   - **Key**: `SENDGRID_API_KEY`
   - **Value**: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (adım 2'de aldığınız API key)
   
   **b) Default From Email:**
   - **Key**: `DEFAULT_FROM_EMAIL`
   - **Value**: SendGrid'de doğrulanmış email adresiniz (örn: `pskbasakseref@gmail.com`)

5. **Eski Gmail environment variable'larını kaldırın** (artık gerekli değil):
   - ❌ `EMAIL_HOST_USER` → Silin
   - ❌ `EMAIL_HOST_PASSWORD` → Silin
   - ❌ `EMAIL_HOST` → Silin
   - ❌ `EMAIL_PORT` → Silin
   - ❌ `EMAIL_USE_TLS` → Silin

6. **Servisi yeniden deploy edin:**
   - Render Dashboard → **Manual Deploy** → **Deploy latest commit**

---

### 5. Local Development (.env dosyası)

Local'de test etmek için `bk_api/.env` dosyasına ekleyin:

```env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=pskbasakseref@gmail.com
```

**⚠️ ÖNEMLİ:** `.env` dosyası git'e commit edilmemeli (`.gitignore`'da olmalı)

---

## ✅ Test Etme

1. **Dependencies yükleyin:**
   ```bash
   cd bk_api
   pip install -r requirements.txt
   ```

2. **Render'da environment variable'ları kontrol edin:**
   - `SENDGRID_API_KEY` ✅
   - `DEFAULT_FROM_EMAIL` ✅

3. **Yeniden deploy edin** (Render otomatik deploy edebilir, manuel de yapabilirsiniz)

4. **Test edin:**
   - Bir randevu oluşturun veya iptal edin
   - Email'lerin gönderildiğini kontrol edin
   - Render logs'unda şu mesajları görmelisiniz:
     - `✅ SendGrid client başarıyla oluşturuldu`
     - `✅ Email başarıyla gönderildi: [email]`

---

## 🔍 Sorun Giderme

### Email gönderilmiyor?

1. **API Key kontrol:**
   - Render'da `SENDGRID_API_KEY` doğru ayarlanmış mı?
   - API Key geçerli mi? (SendGrid Dashboard → API Keys'de kontrol edin)

2. **Email doğrulama:**
   - `DEFAULT_FROM_EMAIL` SendGrid'de doğrulanmış mı?
   - SendGrid Dashboard → Sender Authentication → Single Sender Verification'da kontrol edin

3. **Log kontrolü:**
   - Render logs'unda hata mesajları var mı?
   - `⚠️ SENDGRID_API_KEY ayarlanmamış` → API Key eksik
   - `⚠️ DEFAULT_FROM_EMAIL ayarlanmamış` → Email adresi eksik

### "Unauthorized" hatası?

- API Key yanlış veya süresi dolmuş olabilir
- SendGrid Dashboard'dan yeni API Key oluşturun

### "Forbidden" hatası?

- Email adresi doğrulanmamış olabilir
- SendGrid Dashboard → Sender Authentication'dan doğrulayın

---

## 📊 SendGrid Dashboard

SendGrid Dashboard'da şunları görebilirsiniz:
- **Activity Feed**: Gönderilen email'lerin durumu
- **Stats**: Günlük/haftalık email istatistikleri
- **Settings → API Keys**: API Key yönetimi
- **Settings → Sender Authentication**: Email doğrulama durumu

---

## 💰 Ücretsiz Plan Limitleri

- **100 email/gün** (ücretsiz plan)
- Günlük limit aşılırsa email gönderilmez (bir sonraki güne kadar beklemeniz gerekir)
- Ücretli planlara geçmek isterseniz: https://sendgrid.com/pricing/

---

## 📝 Özet Checklist

- [ ] SendGrid hesabı oluşturuldu
- [ ] API Key oluşturuldu ve kopyalandı
- [ ] Email adresi doğrulandı (Single Sender Verification)
- [ ] Render'da `SENDGRID_API_KEY` eklendi
- [ ] Render'da `DEFAULT_FROM_EMAIL` eklendi
- [ ] Eski Gmail environment variable'ları kaldırıldı
- [ ] `requirements.txt` güncellendi (sendgrid paketi eklendi)
- [ ] Render'da yeniden deploy yapıldı
- [ ] Test email'i gönderildi ve başarılı oldu

---

## 🎉 Tamamlandı!

Artık email'leriniz SendGrid üzerinden gönderilecek. Render'da SMTP portu problemi çözülmüş oldu! 🚀

