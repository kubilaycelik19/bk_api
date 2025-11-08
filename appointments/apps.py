from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appointments'
    
    def ready(self):
        # Django signal işleyicileri import et
        import appointments.signals