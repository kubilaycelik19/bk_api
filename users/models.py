from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    # Kullanıcı adı yerine email ile giriş yapılacak

    email = models.EmailField(unique=True)

    # Roller
    is_patient = models.BooleanField(default=True)  # Hasta rolü


    USERNAME_FIELD = 'email' # Giriş için email kullanılır
    REQUIRED_FIELDS = [] # Zorunlu alanlar (email zaten USERNAME_FIELD olduğu için burada yer almaz). Username zorunluluğu geçici olarak kaldırıldı.

    def __str__(self):
        return self.email

