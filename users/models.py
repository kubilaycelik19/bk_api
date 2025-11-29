from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager

# GÖREV 77: DEĞİŞİKLİĞİ ZORLA (DUMMY COMMENT)

class CustomUserManager(BaseUserManager):
    """
    Email tabanlı özel kullanıcı yöneticimiz.
    Username kullanmıyoruz - sadece email, ad, soyad ve telefon numarası ile çalışıyoruz.
    """

    def _create_user(self, email, password, **extra_fields):
        """
        Email ve şifre ile kullanıcı yaratan temel fonksiyon.
        Username kullanılmıyor - sadece email, ad, soyad ve telefon numarası ile çalışıyoruz.
        """
        if not email:
            raise ValueError('Email alanı zorunludur')

        email = self.normalize_email(email)
        
        # Username'i extra_fields'tan çıkar - artık kullanmıyoruz
        extra_fields.pop('username', None)

        user = self.model(email=email, username=None, **extra_fields)
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

        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    # Kullanıcı adı yerine email ile giriş yapılacak
    
    # Username field'ını override ediyoruz - artık kullanılmıyor
    username = models.CharField(max_length=150, blank=True, null=True, unique=False)
    
    email = models.EmailField(unique=True)
    
    # İletişim bilgileri
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefon Numarası')

    # Roller
    is_patient = models.BooleanField(default=True)  # Hasta rolü

    objects = CustomUserManager()

    USERNAME_FIELD = 'email' # Giriş için email kullanılır
    REQUIRED_FIELDS = [] # Zorunlu alanlar (email zaten USERNAME_FIELD olduğu için burada yer almaz)

    def __str__(self):
        return self.email

