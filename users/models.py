from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    'email' alanını 'username' olarak kullanan
    özel kullanıcı yöneticimiz.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Normal bir kullanıcı yaratır ('username' sormaz).
        """
        if not email:
            raise ValueError("Email alanı zorunludur")

        email = self.normalize_email(email)
        # 'username'i otomatik olarak email'in ilk kısmından alıyoruz
        username = extra_fields.pop('username', email.split('@')[0])

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password) # Şifreyi hash'ler
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Bir superuser (Admin/Psikolog) yaratır.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_patient', False) # Admin hasta değildir

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True olmalıdır.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True olmalıdır.')

        # 'create_user' fonksiyonumuzu (yukarıdaki) kullanarak yaratır
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    # Kullanıcı adı yerine email ile giriş yapılacak

    email = models.EmailField(unique=True)

    # Roller
    is_patient = models.BooleanField(default=True)  # Hasta rolü


    USERNAME_FIELD = 'email' # Giriş için email kullanılır
    REQUIRED_FIELDS = [] # Zorunlu alanlar (email zaten USERNAME_FIELD olduğu için burada yer almaz). Username zorunluluğu geçici olarak kaldırıldı.

    def __str__(self):
        return self.email

