# iYZICO Odeme Entegrasyonu

Bu projede iYZICO odeme gateway'i entegre edilmistir.

## Kurulum

### 1. iyzipay Paketini Kurun

```bash
pip install -r requirements.txt
```

requirements.txt dosyasinda `iyzipay==1.0.36` paketi bulunmaktadir.

### 2. Environment Variables

`.env` dosyaniza asagidaki degiskenleri ekleyin:

```env
# iYZICO Payment Gateway - Sandbox
IYZICO_API_KEY=your-iyzico-sandbox-api-key-here
SANDBOX_SECRET_KEY=your-iyzico-sandbox-secret-key-here
IYZICO_BASE_URL=https://sandbox-api.iyzipay.com

# Frontend URL (callback icin)
FRONTEND_URL=http://localhost:5173
```

**Not:** Production ortami icin:
- `IYZICO_API_KEY` yerine production API key kullanin
- `SANDBOX_SECRET_KEY` yerine production secret key kullanin
- `IYZICO_BASE_URL` degerini `https://api.iyzipay.com` olarak degistirin

### 3. Database Migration

Payment modeli icin migration olusturun ve uygulayin:

```bash
python manage.py makemigrations payments
python manage.py migrate
```

## API Endpoints

### 1. Odeme Baslatma

**POST** `/api/v1/payments/init/`

Odeme islemini baslatir ve iyzico checkout form HTML'i dondurur.

**Request Body:**
```json
{
    "appointment_id": 1,
    "amount": 500.00
}
```

**Response:**
```json
{
    "status": "success",
    "checkout_form_content": "<iframe>...</iframe>",
    "payment_id": "uuid-string"
}
```

### 2. Odeme Kontrol

**POST** `/api/v1/payments/{payment_id}/verify/`

iyzico'dan donen token ile odeme durumunu kontrol eder.

**Request Body:**
```json
{
    "token": "iyzico-token"
}
```

### 3. Callback Endpoint

**POST** `/api/v1/payments/callback/`

iyzico odeme sonrasi buraya POST request yapar.

**Request Body:**
```json
{
    "token": "iyzico-token"
}
```

### 4. Odeme Listesi

**GET** `/api/v1/payments/`

Kullanicinin odemelerini listeler (sadece kendi odemeleri, admin tum odemeleri gorebilir).

### 5. Odeme Detay

**GET** `/api/v1/payments/{payment_id}/`

Belirli bir odemenin detaylarini gosterir.

## Payment Model

Payment modeli asagidaki alanlara sahiptir:

- `id`: UUID (primary key)
- `appointment`: OneToOneField (Appointment ile iliskili)
- `patient`: ForeignKey (Kullanici)
- `amount`: Decimal (Odeme tutari)
- `currency`: CharField (Para birimi, default: TRY)
- `status`: CharField (pending, processing, completed, failed, cancelled, refunded)
- `iyzico_payment_id`: CharField (iyzico'dan gelen payment ID)
- `iyzico_conversation_id`: CharField (iyzico conversation ID)
- `iyzico_basket_id`: CharField (iyzico basket ID)
- `payment_method`: CharField (Odeme yontemi)
- `created_at`: DateTimeField
- `updated_at`: DateTimeField
- `paid_at`: DateTimeField (Odeme yapildigi tarih)
- `error_message`: TextField (Hata mesajlari)

## Frontend Entegrasyonu

Frontend'te odeme yapmak icin:

1. `/api/v1/payments/init/` endpoint'ine POST request atin
2. Dondurulen `checkout_form_content` HTML'ini sayfada gosterin
3. Kullanici odemeyi tamamladiginda, iyzico callback yapar
4. Callback'te donen token ile `/api/v1/payments/{payment_id}/verify/` endpoint'ini cagirin

Ornek frontend kodu:

```javascript
// Odeme baslat
const response = await fetch('/api/v1/payments/init/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
        appointment_id: 1,
        amount: 500.00
    })
});

const data = await response.json();

// Checkout form HTML'ini goster
if (data.status === 'success') {
    document.getElementById('payment-form').innerHTML = data.checkout_form_content;
}
```

## Test Kartlari (Sandbox)

iyzico sandbox ortaminda test icin kullanabileceginiz kredi karti bilgileri:

- **Kart Numarasi:** 5528 7900 0999 9999
- **Son Kullanim:** 12/30 (gelecek bir tarih)
- **CVV:** 123
- **3D Secure Sifresi:** 123456

Daha fazla test karti bilgisi icin iyzico dokumantasyonunu kontrol edin.

## Notlar

- Sandbox ortaminda gercek odeme yapilmaz
- Production'a gecmeden once tum test senaryolarini kontrol edin
- Callback URL'inin frontend URL'i ile uyumlu oldugundan emin olun
- Odeme durumlari admin panelinden takip edilebilir
