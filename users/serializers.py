from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    # Rol alanlarını SADECE OKUNABİLİR yapıyoruz
    # Dışarıdan POST ile 'is_staff' gönderilmesini engelliyoruz
    is_staff = serializers.BooleanField(read_only=True)
    is_patient = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 
            'email', 
            'first_name', 
            'last_name', 
            'phone_number',
            'is_patient',
            'is_staff',
            'password'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

