from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'appointment', 'amount', 'status', 'created_at', 'paid_at']
    list_filter = ['status', 'created_at', 'payment_method']
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__email', 'iyzico_payment_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('id', 'appointment', 'patient', 'amount', 'currency', 'status')
        }),
        ('iYZICO Bilgileri', {
            'fields': ('iyzico_payment_id', 'iyzico_conversation_id', 'iyzico_basket_id', 'payment_method')
        }),
        ('Tarih Bilgileri', {
            'fields': ('created_at', 'updated_at', 'paid_at')
        }),
        ('Hata Bilgileri', {
            'fields': ('error_message',)
        }),
    )