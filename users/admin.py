from django.contrib import admin
from .models import CustomUser

admin.site.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_patient', 'is_staff', 'is_superuser')
    list_filter = ('is_patient', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    list_per_page = 10
