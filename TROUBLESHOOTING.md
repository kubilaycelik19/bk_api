# Render.com 503 Service Unavailable Hatası - Troubleshooting

## 503 Hatası Nedir?

503 Service Unavailable hatası, sunucunun geçici olarak hizmet veremediği anlamına gelir. Render.com'da genellikle şu durumlardan kaynaklanır:

1. **Cold Start (Uyku Modu)** - Free tier'da 15 dakika istek yoksa sunucu uyku moduna geçer
2. **Build Hatası** - Deployment sırasında build başarısız olmuş olabilir
3. **Application Crash** - Uygulama başlatılırken crash oluyor olabilir
4. **Database Bağlantı Sorunu** - Database'e bağlanılamıyor olabilir
5. **Memory/Resource Limit** - Memory limiti aşılmış olabilir

## Hızlı Çözüm Adımları

### 1. Render.com Dashboard'u Kontrol Edin

1. **Render.com Dashboard'a gidin**
   - https://dashboard.render.com
   - Servisinizi seçin

2. **Logs Sekmesini Kontrol Edin**
   - En son log'ları görüntüleyin
   - Hata mesajlarını arayın
   - Build log'larını kontrol edin

3. **Events Sekmesini Kontrol Edin**
   - Son deployment'ları kontrol edin
   - Build başarılı mı?
   - Deployment başarılı mı?

### 2. Servisi Yeniden Deploy Edin

1. **Manual Deploy**
   - Servis sayfasında "Manual Deploy" butonuna tıklayın
   - "Clear build cache & deploy" seçeneğini işaretleyin
   - Deploy'u başlatın

2. **Build Log'larını İzleyin**
   - Build başarılı mı?
   - Herhangi bir hata var mı?

### 3. Environment Variables'ı Kontrol Edin

1. **Environment Sekmesini Kontrol Edin**
   - Tüm environment variable'lar doğru mu?
   - `SECRET_KEY` var mı?
   - `DATABASE_URL` var mı?
   - `DEBUG=False` mu? (Production'da)

### 4. Database Bağlantısını Kontrol Edin

1. **Database Servisini Kontrol Edin**
   - Database servisi çalışıyor mu?
   - Internal URL doğru mu?
   - Connection string doğru mu?

### 5. Health Check Endpoint'ini Test Edin

```bash
curl https://bk-api-evsk.onrender.com/api/v1/health/
```

Beklenen yanıt:
```json
{"status": "ok"}
```

## Yaygın Hatalar ve Çözümleri

### Hata: "Application failed to respond"

**Neden:** Uygulama başlatılamıyor veya crash oluyor

**Çözüm:**
1. Log'ları kontrol edin
2. `DEBUG=False` olduğundan emin olun
3. `SECRET_KEY` environment variable'ı set edilmiş mi kontrol edin
4. Database bağlantısını kontrol edin

### Hata: "Build failed"

**Neden:** Build sırasında hata oluşuyor

**Çözüm:**
1. Build log'larını kontrol edin
2. `requirements.txt` dosyasını kontrol edin
3. Python version'ı kontrol edin
4. Dependencies'leri kontrol edin

### Hata: "Database connection failed"

**Neden:** Database'e bağlanılamıyor

**Çözüm:**
1. Database servisinin çalıştığından emin olun
2. `DATABASE_URL` environment variable'ını kontrol edin
3. Database'in internal URL'ini kullanın (external değil)

### Hata: "Memory limit exceeded"

**Neden:** Memory limiti aşıldı

**Çözüm:**
1. Free tier'da memory limiti 512MB
2. Gerekirse premium plan'a geçin
3. Veya memory kullanımını optimize edin

## Cold Start Sorunu

Free tier'da sunucu 15 dakika istek almadığında uyku moduna geçer. İlk istekte 30-90 saniye sürebilir.

**Çözüm:**
1. **UptimeRobot kullanın** (önerilen)
   - Her 5 dakikada bir health check yapın
   - Sunucuyu uyanık tutun
   - Detaylar: `RENDER_SETUP.md`

2. **Premium Plan'a Geçin**
   - Sunucu sürekli aktif kalır
   - Cold start sorunu olmaz

## Debug Modu

Production'da `DEBUG=False` olmalı. Ama geçici olarak debug modunu açarak hatayı görebilirsiniz:

1. Environment variable'da `DEBUG=True` yapın
2. Servisi yeniden deploy edin
3. Log'ları kontrol edin
4. Hatayı gördükten sonra `DEBUG=False` yapın

**⚠️ DİKKAT:** Production'da `DEBUG=True` bırakmayın! Güvenlik riski oluşturur.

## İletişim

Sorun devam ederse:
1. Render.com support'a başvurun
2. Log'ları paylaşın
3. Environment variable'ları kontrol edin
4. Build log'larını kontrol edin

