from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager

# GÖREV 77: DEĞİŞİKLİĞİ ZORLA (DUMMY COMMENT)

class CustomUserManager(BaseUserManager):
    """
    'email' alanını 'username' olarak kullanan
    özel kullanıcı yöneticimiz. (DOĞRU VERSİYON)
    """

    def _create_user(self, email, password, **extra_fields):
        """
        Email ve şifre ile kullanıcı yaratan temel fonksiyon.
        """
        if not email:
            raise ValueError('Email alanı zorunludur')

        email = self.normalize_email(email)

        # username'i extra_fields'tan al, yoksa email'den üret
        username = extra_fields.pop('username', email.split('@')[0])

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password) # Şifreyi GÜVENLİ olarak hash'ler
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Normal bir kullanıcı (Hasta) yaratır.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_patient', True) # GÖREV 51'deki güvenlik
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Bir superuser (Admin/Psikolog) yaratır.
        Bu imza (signature) 'createsuperuser --noinput' komutuyla
        artık tam uyumludur.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_patient', False) # Admin hasta değildir

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True olmalıdır.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True olmalıdır.')

        # Biz sadece email ve password'ü _create_user'a yolluyoruz.
        # _create_user da username'i extra_fields'tan 'pop' ile çekecek.

        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    # Kullanıcı adı yerine email ile giriş yapılacak

    email = models.EmailField(unique=True)

    # Roller
    is_patient = models.BooleanField(default=True)  # Hasta rolü


    USERNAME_FIELD = 'email' # Giriş için email kullanılır
    REQUIRED_FIELDS = [] # Zorunlu alanlar (email zaten USERNAME_FIELD olduğu için burada yer almaz). Username zorunluluğu geçici olarak kaldırıldı.

    def __str__(self):
        return self.email

