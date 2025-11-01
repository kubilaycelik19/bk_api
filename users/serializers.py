from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'is_patient', 'password']
        # password alanını dahil etmiyoruz, çünkü şifreler hassas bilgilerdir ve genellikle API üzerinden gönderilmez veya alınmaz

