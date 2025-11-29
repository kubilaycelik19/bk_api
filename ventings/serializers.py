from rest_framework import serializers
from .models import Venting
from users.serializers import UserSerializer

class VentingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Venting
        fields = ['id', 'user', 'content', 'created_at', 'mood']
        read_only_fields = ['id', 'created_at']

        def __str__(self):
            return self.content