# Hosting ve Email Gönderme Seçenekleri

Email göndermek kritik bir özellikse, aşağıdaki seçenekleri değerlendirebilirsiniz.

## Seçenek 1: Render.com Ücretli Plan (Önerilen - Kolay)

### Avantajlar:
- ✅ Render.com'da kalırsınız (migration yok)
- ✅ SMTP bağlantıları çalışır (ücretli planda engel yok)
- ✅ Gmail SMTP'yi direkt kullanabilirsiniz
- ✅ Kolay kurulum (sadece plan değiştirme)
- ✅ Mevcut deployment'ınız çalışmaya devam eder

### Dezavantajlar:
- ❌ Ücretli ($7/ay başlangıç)
- ❌ Render.com'a bağımlı kalırsınız

### Fiyat:
- **Starter Plan**: $7/ay (512MB RAM, 0.1 CPU)
- **Standard Plan**: $25/ay (2GB RAM, 1 CPU)

### Kurulum:
1. Render.com Dashboard → Servisiniz
2. "Change Plan" → "Starter" veya "Standard" seçin
3. Ödeme bilgilerini girin
4. Deploy'u yeniden yapın
5. Gmail SMTP ayarlarınız çalışacak

### Sonuç:
**Render.com ücretli planda Gmail SMTP direkt çalışır. Kod değişikliği gerekmez.**

---

## Seçenek 2: Google Cloud Platform (GCP) - Free Tier

### Avantajlar:
- ✅ Ücretsiz tier var (Always Free)
- ✅ SMTP bağlantıları çalışır
- ✅ Gmail SMTP'yi direkt kullanabilirsiniz
- ✅ Güvenilir ve ölçeklenebilir
- ✅ $300 kredi (ilk 90 gün)

### Dezavantajlar:
- ❌ Migration gerekiyor (Render'dan GCP'ye)
- ❌ Biraz daha kompleks kurulum
- ❌ Free tier limitleri var (günlük)

### Free Tier Limitleri:
- **Cloud Run**: Ayda 2 milyon request (ücretsiz)
- **Cloud SQL**: 1 instance (ücretsiz, sınırlı)
- **SMTP**: Çalışır (limit yok)

### Kurulum:

#### 1. GCP'de Proje Oluşturun
```bash
# GCP Console'da proje oluşturun
# https://console.cloud.google.com
```

#### 2. Cloud Run'da Deploy Edin
```bash
# Dockerfile oluşturun
# Cloud Run'a deploy edin
```

#### 3. Environment Variables
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Fiyat:
- **Free Tier**: $0/ay (sınırlı kullanım)
- **Paid**: Kullandığınız kadar öde ($0.00002400/request)

### Sonuç:
**GCP free tier'da Gmail SMTP çalışır. Migration gerekiyor ama ücretsiz.**

---

## Seçenek 3: AWS (Amazon Web Services) - Free Tier

### Avantajlar:
- ✅ Ücretsiz tier var (12 ay)
- ✅ SMTP bağlantıları çalışır
- ✅ AWS SES kullanabilirsiniz (ücretsiz, 62,000 email/ay)
- ✅ Güvenilir ve ölçeklenebilir
- ✅ $300 kredi (ilk 12 ay)

### Dezavantajlar:
- ❌ Migration gerekiyor (Render'dan AWS'ye)
- ❌ Biraz daha kompleks kurulum
- ❌ Free tier limitleri var (12 ay)

### Free Tier Limitleri:
- **EC2**: 750 saat/ay (ücretsiz, 12 ay)
- **Elastic Beanstalk**: Ücretsiz (sadece EC2 ücreti)
- **AWS SES**: 62,000 email/ay (ücretsiz, EC2'den)

### Kurulum:

#### 1. AWS'de Hesap Oluşturun
```bash
# AWS Console'da hesap oluşturun
# https://console.aws.amazon.com
```

#### 2. Elastic Beanstalk'da Deploy Edin
```bash
# Django uygulamanızı Elastic Beanstalk'a deploy edin
# Veya EC2'ye manuel deploy edin
```

#### 3. AWS SES Kullanın (Önerilen)
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-ses-smtp-username'
EMAIL_HOST_PASSWORD = 'your-ses-smtp-password'
```

### Fiyat:
- **Free Tier**: $0/ay (12 ay, sınırlı kullanım)
- **Paid**: Kullandığınız kadar öde

### Sonuç:
**AWS free tier'da AWS SES çalışır (62,000 email/ay ücretsiz). Migration gerekiyor.**

---

## Seçenek 4: Railway.app - Free Tier

### Avantajlar:
- ✅ Ücretsiz tier var ($5 kredi/ay)
- ✅ SMTP bağlantıları çalışır
- ✅ Gmail SMTP'yi direkt kullanabilirsiniz
- ✅ Kolay kurulum (GitHub'dan deploy)
- ✅ Render.com'a benzer

### Dezavantajlar:
- ❌ Free tier limiti var ($5 kredi/ay)
- ❌ Migration gerekiyor

### Free Tier Limitleri:
- **$5 kredi/ay** (ücretsiz)
- **SMTP**: Çalışır (limit yok)

### Kurulum:
1. Railway.app'e kaydolun
2. GitHub repo'nuzu bağlayın
3. Deploy edin
4. Gmail SMTP ayarlarınız çalışacak

### Fiyat:
- **Free Tier**: $5 kredi/ay (ücretsiz)
- **Paid**: Kullandığınız kadar öde

### Sonuç:
**Railway.app free tier'da Gmail SMTP çalışır. Migration gerekiyor.**

---

## Seçenek 5: SendGrid/Mailgun (Render Free Tier'da Çalışır) ⭐ EN KOLAY

### Avantajlar:
- ✅ Render.com free tier'da kalırsınız
- ✅ Migration yok
- ✅ SendGrid/Mailgun ücretsiz
- ✅ SMTP yerine HTTPS API kullanır (engel yok)
- ✅ Kolay kurulum (5 dakika)
- ✅ Güvenilir servis

### Dezavantajlar:
- ❌ Gmail SMTP kullanamazsınız (SendGrid/Mailgun kullanırsınız)
- ❌ Üçüncü parti servis

### Free Tier Limitleri:
- **SendGrid**: 100 email/gün (ücretsiz)
- **Mailgun**: 5,000 email/ay (ücretsiz)

### Kurulum:
1. SendGrid'a kaydolun (ücretsiz)
2. API Key oluşturun
3. Render.com'da environment variables'ı set edin
4. Deploy'u yeniden yapın
5. Çalışır!

### Fiyat:
- **Free Tier**: $0/ay (sınırlı kullanım)
- **Paid**: İhtiyacınıza göre

### Sonuç:
**SendGrid/Mailgun Render free tier'da çalışır. Migration yok, kolay kurulum.**

---

## Karşılaştırma Tablosu

| Özellik | Render Paid | GCP Free | AWS Free | Railway Free | SendGrid |
|---------|-------------|----------|----------|--------------|----------|
| **Fiyat** | $7/ay | $0/ay | $0/ay | $0/ay | $0/ay |
| **Migration** | ❌ Yok | ✅ Gerekli | ✅ Gerekli | ✅ Gerekli | ❌ Yok |
| **Gmail SMTP** | ✅ Çalışır | ✅ Çalışır | ✅ Çalışır | ✅ Çalışır | ❌ Yok |
| **Kurulum** | ⭐⭐ Kolay | ⭐⭐⭐ Orta | ⭐⭐⭐ Orta | ⭐⭐ Kolay | ⭐ Çok Kolay |
| **Email Limit** | Sınırsız | Sınırsız | 62,000/ay | Sınırsız | 100/gün |
| **Güvenilirlik** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## Öneri

### Senaryo 1: Hızlı Çözüm İstiyorsanız (5 dakika)
**→ SendGrid/Mailgun kullanın**
- Migration yok
- Render free tier'da kalın
- Kolay kurulum
- Ücretsiz

### Senaryo 2: Gmail SMTP Kullanmak İstiyorsanız
**→ Render.com ücretli plan**
- Migration yok
- Gmail SMTP direkt çalışır
- Kolay kurulum
- $7/ay

### Senaryo 3: Ücretsiz ve Gmail SMTP İstiyorsanız
**→ GCP veya AWS free tier**
- Migration gerekiyor
- Gmail SMTP çalışır
- Ücretsiz
- Biraz kompleks kurulum

---

## Sonuç

**Email göndermek kritikse:**

1. **En Kolay**: SendGrid/Mailgun (Render free tier'da çalışır, migration yok)
2. **Gmail SMTP + Kolay**: Render.com ücretli plan ($7/ay, migration yok)
3. **Gmail SMTP + Ücretsiz**: GCP/AWS free tier (migration gerekiyor)

**Benim önerim**: SendGrid kullanın. Migration yok, kolay kurulum, ücretsiz, Render free tier'da çalışır.

