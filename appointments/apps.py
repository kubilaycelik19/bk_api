from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appointments'
    
    def ready(self):
        # Django signal işleyicileri import et
        print("🚀 [APPS] AppointmentsConfig.ready() çağrıldı - Signal'ler yükleniyor...")
        logger.info("🚀 AppointmentsConfig.ready() çağrıldı - Signal'ler yükleniyor...")
        try:
            import appointments.signals
            print("✅ [APPS] Signal'ler başarıyla yüklendi")
            logger.info("✅ Signal'ler başarıyla yüklendi")
        except Exception as e:
            print(f"❌ [APPS] Signal'ler yüklenirken hata: {str(e)}")
            logger.error(f"❌ Signal'ler yüklenirken hata: {str(e)}", exc_info=True)