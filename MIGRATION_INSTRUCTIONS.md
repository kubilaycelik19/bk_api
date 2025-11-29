# Payment Migration Talimatlari

Payment tablosu olusturmak icin asagidaki adimlari takip edin:

## 1. Virtual Environment'i Aktif Edin

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

## 2. Migration Dosyalarini Olusturun

```bash
cd bk_api
python manage.py makemigrations payments
```

## 3. Migration'lari Uygulayin

```bash
python manage.py migrate
```

## Not

Eger "no such table: payments_payment" hatasi aliyorsaniz, migration'lari yukaridaki adimlarla calistirmalisiniz.

Payment tablosu olusturulduktan sonra randevu olusturma hatasi duzelecektir.
