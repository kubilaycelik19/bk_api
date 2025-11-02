"""
Custom Exception Handler for Django REST Framework
Tutarlı hata yönetimi için özel exception handler
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Django REST Framework için özel exception handler.
    Tüm hataları tutarlı bir formatta döndürür.
    """
    # REST Framework'ün varsayılan exception handler'ını çağır
    response = exception_handler(exc, context)

    # Eğer response None ise (yani REST Framework bu hatayı handle edemiyorsa)
    # Django'nun standart hatalarını handle et
    if response is None:
        if isinstance(exc, Http404):
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "İstenen kaynak bulunamadı.",
                        "detail": str(exc)
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        if isinstance(exc, DjangoValidationError):
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Geçersiz veri.",
                        "detail": exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Beklenmeyen hatalar için genel hata mesajı
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return Response(
            {
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Sunucuda bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
                    "detail": str(exc) if exc else None
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # REST Framework'ün response'unu al ama formatını değiştir
    custom_response_data = {
        "success": False,
        "error": {
            "code": get_error_code(response.status_code),
            "message": get_error_message(exc, response.status_code),
            "detail": response.data if isinstance(response.data, (dict, list)) else {"detail": str(response.data)}
        }
    }

    # Eğer response.data bir dict ise ve içinde 'detail' varsa, onu kullan
    if isinstance(response.data, dict):
        if 'detail' in response.data:
            custom_response_data["error"]["message"] = response.data['detail']
        # Field-specific errors için
        elif len(response.data) == 1:
            for field, errors in response.data.items():
                if isinstance(errors, list):
                    custom_response_data["error"]["detail"] = {field: errors[0] if errors else "Geçersiz değer"}
                    custom_response_data["error"]["message"] = f"{field}: {errors[0] if errors else 'Geçersiz değer'}"
                else:
                    custom_response_data["error"]["detail"] = {field: str(errors)}
                    custom_response_data["error"]["message"] = f"{field}: {str(errors)}"

    return Response(custom_response_data, status=response.status_code)


def get_error_code(status_code):
    """HTTP status code'a göre error code döndür"""
    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR",
    }
    return error_codes.get(status_code, "UNKNOWN_ERROR")


def get_error_message(exc, status_code):
    """Hata türüne göre Türkçe hata mesajı döndür"""
    default_messages = {
        400: "Geçersiz istek. Lütfen gönderdiğiniz verileri kontrol edin.",
        401: "Kimlik doğrulama gerekli. Lütfen giriş yapın.",
        403: "Bu işlem için yetkiniz bulunmamaktadır.",
        404: "İstenen kaynak bulunamadı.",
        405: "Bu HTTP metodu bu endpoint için kullanılamaz.",
        409: "İşlem çakışma oluşturdu. Lütfen tekrar deneyin.",
        422: "İşlenemeyen veri. Lütfen gönderdiğiniz verileri kontrol edin.",
        500: "Sunucuda bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
    }
    return default_messages.get(status_code, "Bir hata oluştu.")

