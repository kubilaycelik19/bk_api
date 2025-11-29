from django.contrib import admin
from .models import AvailableTimeSlot, Appointment, AppointmentPrice

@admin.register(AvailableTimeSlot)
class AvailableTimeSlotAdmin(admin.ModelAdmin):
    list_display = ['id', 'psychologist', 'start_time', 'end_time', 'is_booked']
    list_filter = ['is_booked', 'start_time']
    search_fields = ['psychologist__first_name', 'psychologist__last_name', 'psychologist__email']
    date_hierarchy = 'start_time'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'time_slot', 'created_at']
    list_filter = ['created_at']
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__email']
    date_hierarchy = 'created_at'

@admin.register(AppointmentPrice)
class AppointmentPriceAdmin(admin.ModelAdmin):
    list_display = ['hourly_rate', 'updated_at', 'updated_by']
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        # Eger zaten bir fiyat ayari varsa, yeni ekleme yapilamasin
        if AppointmentPrice.objects.exists():
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        # Fiyat ayari silinemesin (silinirse problem olur)
        return False
