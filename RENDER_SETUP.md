# Render.com Free Tier Cold Start Çözümü

## Sorun
Render.com free tier'da sunucular 15 dakika istek almadığında uyku moduna geçer. Bu da ilk istekte 30-90 saniye cold start süresine neden olur.

## Çözüm: UptimeRobot (Ücretsiz)

### Adımlar:

1. **UptimeRobot'a kaydolun**
   - https://uptimerobot.com adresine gidin
   - Ücretsiz hesap oluşturun (50 monitor limiti)

2. **Yeni Monitor Oluşturun**
   - Dashboard → "Add New Monitor"
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: BK API Health Check
   - **URL**: `https://bk-api-evsk.onrender.com/api/v1/health/`
   - **Monitoring Interval**: 5 minutes (veya daha sık)
   - **Alert Contacts**: Email ekleyin (opsiyonel)

3. **Kaydet**
   - "Create Monitor" butonuna tıklayın
   - Artık her 5 dakikada bir API'ye istek atılacak
   - Bu sayede sunucu uyku moduna geçmeyecek

### Alternatif: Cron-Job.org (Ücretsiz)

1. https://cron-job.org adresine gidin
   - Ücretsiz hesap oluşturun
   - Yeni cron job oluşturun
   - URL: `https://bk-api-evsk.onrender.com/api/v1/health/`
   - Interval: Her 5 dakikada bir
   - HTTP Method: GET

## Sonuç

UptimeRobot veya benzeri bir servis kullanarak:
- ✅ Sunucu sürekli aktif kalır
- ✅ Cold start sorunu çözülür
- ✅ İlk istekte timeout olmaz
- ✅ Ücretsiz çözüm

## Notlar

- UptimeRobot free tier'da 50 monitor limiti var (yeterli)
- Monitoring interval'i 5 dakika yeterli (15 dakikadan az)
- Health check endpoint'i çok hafif, veritabanı sorgusu yapmıyor
- Bu çözüm %100 çalışır, domain değişikliği gerekmez

