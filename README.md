Kullanılan Teknolojiler
Backend: Python 3.11, Django 5.2

API: Django REST Framework (DRF)

Kimlik Doğrulama (Authentication): djangorestframework-simplejwt (JSON Web Tokens)

Veritabanı: PostgreSQL (Canlıda) / SQLite3 (Yerelde)

Sunucu (Server): Gunicorn

Canlı Yayın (Deployment): Render.com

Güvenlik: django-cors-headers (CORS), python-dotenv (Gizli anahtarlar)

Statik Dosyalar (Admin Paneli): whitenoise

Ana Özellikler
Rol Bazlı İzinler: Sistemde iki ana rol vardır:

Admin (Admin/is_staff=True): Müsait zaman slotları oluşturabilir, silebilir, güncelleyebilir ve tüm randevuları listeleyebilir.

Hasta (Patient/is_patient=True): Sadece müsait slotları listeleyebilir, sadece kendine ait randevuları alabilir, görebilir veya silebilir.

Güvenli Kimlik Doğrulama: JWT (Access + Refresh Token) sistemi ile güvenli giriş.

Otomatik Slot Yönetimi: Bir hasta randevu aldığında (POST /appointments/), o slot (AvailableTimeSlot) otomatik olarak is_booked=True olarak işaretlenir ve listeden düşer.

Temiz API Mimarisi: ModelViewSet, CustomUserManager ve özel Permission (İzin) sınıfları kullanılarak temiz ve modüler bir yapı oluşturulmuştur.
---------------------------------------------------------------------------------------------------------------------------------------------------------

Yerel (Lokal) Kurulum ve Çalıştırma
Projeyi kendi bilgisayarınızda çalıştırmak için:

Repoyu klonlayın:

Bash

git clone https://github.com/kubilaycelik19/bk_api.git
cd bk_api
Sanal ortam (virtual environment) oluşturun ve aktif edin:

Bash

python -m venv venv
source venv/bin/activate  # (Mac/Linux)
# veya
venv\Scripts\activate     # (Windows)
Gereksinimleri kurun:

Bash

pip install -r requirements.txt
.env dosyasını oluşturun:

Ana dizinde (manage.py'nin olduğu dizinde) .env.example dosyasını .env olarak kopyalayın.

.env dosyasının içini kendi SECRET_KEY'iniz ile doldurun. (Not: Bu projede .env.example dosyası henüz eklenmemiştir. DEBUG=True ve SECRET_KEY='...' içeren bir .env dosyası oluşturulmalıdır.)

Veritabanını oluşturun (Migration):

Bash

python manage.py migrate
Admin kullanıcısı oluşturun:

Bash

python manage.py createsuperuser
Sunucuyu çalıştırın:

Bash

python manage.py runserver

API Endpoint (Adres) Haritası
Tüm adreslerin başında https://bk-api-evsk.onrender.com/ bulunur.

1. Kimlik Doğrulama (Authentication)
POST /api/token/
Açıklama: Sisteme giriş yapmak için kullanılır. email ve password alır.

Başarılı Cevap (200 OK): access ve refresh token'larını döndürür.

Body (JSON):

JSON

{
    "email": "admin@mail.com",
    "password": "sifre123"
}
2. Kullanıcı Yönetimi (/api/v1/)
POST /api/v1/users/
Açıklama: Yeni bir Hasta (Patient) kullanıcısı oluşturur (Kayıt Ol).

İzin: Herkese açık (AllowAny).

Güvenlik: is_staff veya is_patient yollansa bile, perform_create metodu sayesinde her zaman is_staff=False ve is_patient=True olarak oluşturulur.

Body (JSON):

JSON

{
    "email": "yeni_hasta@mail.com",
    "username": "yenihasta",
    "password": "GuvenliSifre123",
    "first_name": "Yeni",
    "last_name": "Hasta"
}
GET /api/v1/users/
Açıklama: Tüm kullanıcıları listeler.

İzin: Sadece Admin (IsAdminUser).

GET /api/v1/users/me/
Açıklama: Giriş yapmış (token sahibi) kullanıcının kendi detaylarını döndürür.

İzin: Sadece giriş yapmış kullanıcılar (IsAuthenticated).

3. Müsait Slotlar (/api/v1/)
GET /api/v1/slots/
Açıklama: Sadece müsait (is_booked=False) olan zaman slotlarını listeler.

İzin: Giriş yapmış tüm kullanıcılar (Admin ve Hasta).

POST /api/v1/slots/
Açıklama: Yeni bir müsait zaman slotu oluşturur.

İzin: Sadece Admin (IsAdminOrReadOnly).

Body (JSON):

JSON

{
    "start_time": "2025-12-10T14:00:00Z",
    "end_time": "2025-12-10T15:00:00Z"
}
4. Randevular (/api/v1/)
GET /api/v1/appointments/
Açıklama: Randevuları listeler.

İzin (Akıllı):

Admin: Tüm randevuları görür.

Hasta (Patient): Sadece kendi randevularını görür.

POST /api/v1/appointments/
Açıklama: Yeni bir randevu alır.

İzin: Sadece giriş yapmış kullanıcılar (IsAuthenticatedOrOptions).

İş Mantığı:

perform_create metodu, time_slot_id ile istenen slotu bulur.

Slotun is_booked olup olmadığını kontrol eder.

Slotu is_booked=True olarak günceller.

Randevuyu, patient=request.user (giriş yapan hasta) olarak oluşturur.

Body (JSON):

JSON

{
    "time_slot_id": 5,
    "notes": "Bu bir test randevusudur."
}

