from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import uuid
import logging
import json

from .models import Payment
from .serializers import PaymentSerializer, PaymentInitSerializer
from .iyzico_service import IyzicoService
from appointments.models import Appointment

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Payment viewset - Odeme islemleri
    ReadOnlyModelViewSet: Sadece GET (list, retrieve) islemlerini destekler
    Create/Update/Delete islemleri ozel action'larla yapilir
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Kullanici sadece kendi odemelerini gorebilir
        Admin tum odemeleri gorebilir
        """
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(patient=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='init')
    def init_payment(self, request):
        """
        Odeme islemini baslatir ve iyzico checkout form HTML'i dondurur
        POST /api/v1/payments/init/
        Body: {
            "appointment_id": 1,
            "amount": 500.00
        }
        """
        serializer = PaymentInitSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        appointment_id = serializer.validated_data['appointment_id']
        # Eger amount gonderildiyse kullan, yoksa randevu suresine gore hesapla
        requested_amount = serializer.validated_data.get('amount')
        
        try:
            appointment = Appointment.objects.get(id=appointment_id)
            
            # Amount hesapla: Eger gonderilmediyse randevu suresine gore hesapla
            if requested_amount:
                amount = requested_amount
            else:
                amount = appointment.calculate_price()
            
            # Payment'i al veya olustur (signal ile otomatik olusturulmus olmalı)
            if hasattr(appointment, 'payment'):
                existing_payment = appointment.payment
                if existing_payment.status == 'completed':
                    return Response(
                        {'error': 'Bu randevu icin odeme zaten yapilmis.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Mevcut payment'i kullan ve amount'u guncelle (eğer değiştiyse)
                payment = existing_payment
                if payment.amount != amount:
                    payment.amount = amount
                    payment.save()
                logger.info(f"Mevcut payment kullaniliyor - ID: {payment.id}, Status: {payment.status}")
            else:
                # Payment yoksa olustur (signal calismadiysa yedek olarak)
                payment = Payment.objects.create(
                    appointment=appointment,
                    patient=request.user,
                    amount=amount,
                    currency='TRY',
                    status='pending'
                )
                logger.warning(f"Payment signal ile olusturulmamisti, manuel olusturuldu - ID: {payment.id}")
            
            # iyzico servisi
            iyzico_service = IyzicoService()
            
            # Benzersiz ID'ler
            conversation_id = str(payment.id)
            basket_id = str(payment.id)
            
            # Callback URL (iyzico odeme sonrasi backend'e gelecek, backend frontend'e redirect yapacak)
            # Backend callback URL'ini al (DRF authentication'dan muaf olmak icin farkli path kullan)
            backend_base_url = request.build_absolute_uri('/')[:-1]  # Son '/' karakterini kaldır
            callback_url = f"{backend_base_url}/payments/callback/"
            
            # Hasta bilgileri
            patient = request.user
            buyer = {
                'id': str(patient.id),
                'name': f"{patient.first_name or ''} {patient.last_name or ''}".strip() or patient.email.split('@')[0],
                'surname': patient.last_name or '',
                'gsmNumber': patient.phone_number or '+905550000000',
                'email': patient.email,
                'identityNumber': '11111111111',  # iyzico test icin gerekli (sandbox)
                'lastLoginDate': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'registrationDate': patient.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'registrationAddress': 'Adres bilgisi yok',
                'ip': request.META.get('REMOTE_ADDR', '127.0.0.1'),
                'city': 'Istanbul',
                'country': 'Turkey',
                'zipCode': '34000'
            }
            
            # Adres bilgileri
            address = {
                'contactName': buyer['name'],
                'city': 'Istanbul',
                'country': 'Turkey',
                'address': 'Adres bilgisi yok',
                'zipCode': '34000'
            }
            
            # Sepet urunleri
            basket_items = [{
                'id': str(appointment.id),
                'name': f'Randevu - {appointment.time_slot.start_time.strftime("%d.%m.%Y %H:%M")}',
                'category1': 'Randevu',
                'category2': 'Psikolog Randevusu',
                'itemType': 'VIRTUAL',
                'price': str(amount)
            }]
            
            # iyzico payment request
            payment_data = {
                'conversation_id': conversation_id,
                'price': str(amount),
                'paid_price': str(amount),
                'currency': 'TRY',
                'basket_id': basket_id,
                'callback_url': callback_url,
                'enabled_installments': [],
                'buyer': buyer,
                'shipping_address': address,
                'billing_address': address,
                'basket_items': basket_items
            }
            
            result = iyzico_service.create_payment_request(payment_data)
            
            if result['status'] == 'success':
                # Payment'i guncelle
                payment.iyzico_conversation_id = conversation_id
                payment.iyzico_basket_id = basket_id
                payment.status = 'processing'
                payment.save()
                
                checkout_content = result.get('checkout_form_content', '')
                logger.info(f"Checkout form content length: {len(checkout_content) if checkout_content else 0}")
                
                if not checkout_content:
                    logger.error("Checkout form content bos!")
                    payment.status = 'failed'
                    payment.error_message = 'iyzico checkout form icerigi alinamadi'
                    payment.save()
                    return Response(
                        {'error': 'Odeme formu yuklenemedi. Lutfen tekrar deneyin.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                return Response({
                    'status': 'success',
                    'checkout_form_content': checkout_content,
                    'payment_id': str(payment.id)
                })
            else:
                payment.status = 'failed'
                payment.error_message = result.get('error_message', 'Bilinmeyen hata')
                payment.save()
                
                return Response(
                    {'error': result.get('error_message', 'Odeme baslatilamadi.')},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Randevu bulunamadi.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Odeme baslatma hatasi: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Odeme baslatilirken bir hata olustu.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='verify')
    def verify_payment(self, request, pk=None):
        """
        iyzico'dan donen token ile odeme durumunu kontrol eder
        POST /api/v1/payments/{id}/verify/
        Body: {
            "token": "iyzico_token"
        }
        """
        try:
            payment = self.get_object()
        except Exception as e:
            logger.error(f"Payment bulunamadi: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Odeme kaydi bulunamadi.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token gerekli.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            iyzico_service = IyzicoService()
            result = iyzico_service.retrieve_payment(token)
            
            # Result'un valid olduğunu kontrol et
            if not isinstance(result, dict):
                payment.status = 'failed'
                payment.error_message = 'Geçersiz iyzico yanıtı'
                payment.save()
                return Response(
                    {'error': 'Geçersiz iyzico yanıtı'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            result_status = result.get('status')
            if not result_status:
                payment.status = 'failed'
                payment.error_message = 'Status bilgisi bulunamadi'
                payment.save()
                return Response(
                    {'error': 'Status bilgisi bulunamadi'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            if result_status == 'success':
                # Odeme basarili
                payment.status = 'completed'
                payment.iyzico_payment_id = result.get('payment_id')
                payment.payment_method = result.get('payment_method', 'card')
                payment.paid_at = timezone.now()
                payment.save()
                
                # Randevu status'unu 'paid' olarak guncelle
                appointment = payment.appointment
                appointment.status = 'paid'
                appointment.save()
                
                # Ödeme tamamlandı email'i gönder
                try:
                    from appointments.email_service import send_payment_completed_email
                    send_payment_completed_email(payment)
                    logger.info(f"Ödeme tamamlanma email'i gönderildi (verify) - Payment ID: {payment.id}")
                except Exception as e:
                    logger.error(f"Ödeme tamamlanma email'i gönderilirken hata (verify): {str(e)}", exc_info=True)
                    # Email hatası ödeme işlemini engellememeli
                
                return Response({
                    'status': 'success',
                    'message': 'Odeme basariyla tamamlandi.',
                    'payment': PaymentSerializer(payment).data
                })
            elif result_status == 'failed':
                # Odeme basarisiz
                payment.status = 'failed'
                payment.error_message = result.get('error_message', 'Odeme basarisiz')
                payment.save()
                
                return Response(
                    {
                        'status': 'failed',
                        'error': result.get('error_message', 'Odeme basarisiz')
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif result_status == 'error':
                # iyzico'dan hata geldi
                payment.status = 'failed'
                error_msg = result.get('error_message', 'Odeme kontrol edilemedi')
                payment.error_message = error_msg
                payment.save()
                
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            else:
                # Beklenmeyen status degeri (defensive programming)
                logger.warning(f"Beklenmeyen iyzico status degeri: {result_status}")
                payment.status = 'failed'
                error_msg = f"Beklenmeyen durum: {result_status}"
                payment.error_message = error_msg
                payment.save()
                
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Odeme kontrol hatasi: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Odeme kontrol edilirken bir hata olustu.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@csrf_exempt  # CSRF kontrolünü devre dışı bırak (iyzico callback'leri için)
@require_http_methods(["GET", "POST"])  # Sadece GET ve POST metodlarına izin ver
def payment_callback(request):
    """
    iyzico callback endpoint (Normal Django view - DRF'den tamamen bağımsız)
    iyzico odeme sonrasi buraya POST request yapar
    Bu endpoint public olmalidir cunku iyzico'dan gelen callback authentication yapmaz.
    Guvenlik: Token ve conversation_id ile dogrulama yapilir.
    
    NOT: Bu endpoint DRF authentication kontrolünden geçmez çünkü:
    - Normal Django view (DRF ViewSet değil)
    - @csrf_exempt ile CSRF kontrolü yok
    - /payments/callback/ path'i DRF router'ının dışında
    """
    # İlk log - callback'in çağrıldığını göster
    logger.info(f"🔔 Payment callback endpoint'e erisildi - Method: {request.method}, Path: {request.path}")
    print(f"🔔 [CALLBACK] Payment callback endpoint'e erisildi - Method: {request.method}, Path: {request.path}")
    # Request body'den veya query string'den token'i al (iyzico callback GET veya POST ile gelebilir)
    if request.method == 'POST':
        # POST isteği için body'den veya form data'dan token'i al
        try:
            if request.content_type and 'application/json' in request.content_type:
                body_data = json.loads(request.body.decode('utf-8'))
                token = body_data.get('token')
            else:
                # Form data veya URL-encoded data
                token = request.POST.get('token')
        except:
            token = None
    else:
        # GET isteği için query string'den token'i al
        token = request.GET.get('token')
    
    logger.info(f"Payment callback alindi - Method: {request.method}, Token: {token[:20] if token else 'None'}...")
    
    if not token:
        # Token yoksa frontend'e hata ile redirect yap
        frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'
        redirect_url = f"{frontend_url}/payment/callback?status=error&error=Token gerekli"
        return HttpResponseRedirect(redirect_url)
    
    try:
        iyzico_service = IyzicoService()
        result = iyzico_service.retrieve_payment(token)
        
        # Result'un valid olduğunu kontrol et
        if not isinstance(result, dict) or 'status' not in result:
            frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'
            redirect_url = f"{frontend_url}/payment/callback?status=error&error=Gecersiz iyzico yaniti"
            return HttpResponseRedirect(redirect_url)
        
        if result['status'] == 'success':
            conversation_id = result.get('conversation_id')
            basket_id = result.get('basket_id')
            
            # Payment'i conversation_id veya basket_id ile bul
            payment = None
            if conversation_id:
                try:
                    payment = Payment.objects.get(iyzico_conversation_id=conversation_id)
                    logger.info(f"Payment conversation_id ile bulundu - Payment ID: {payment.id}, Conversation ID: {conversation_id}")
                except Payment.DoesNotExist:
                    logger.warning(f"Payment conversation_id ile bulunamadi: {conversation_id}")
            
            # Eger conversation_id ile bulunamazsa basket_id ile dene
            if not payment and basket_id:
                try:
                    payment = Payment.objects.get(iyzico_basket_id=basket_id)
                    logger.info(f"Payment basket_id ile bulundu - Payment ID: {payment.id}, Basket ID: {basket_id}")
                except Payment.DoesNotExist:
                    logger.warning(f"Payment basket_id ile bulunamadi: {basket_id}")
                except Payment.MultipleObjectsReturned:
                    # Birden fazla payment varsa ilkini al
                    payment = Payment.objects.filter(iyzico_basket_id=basket_id).first()
                    logger.warning(f"Birden fazla payment bulundu, ilki kullanildi - Payment ID: {payment.id if payment else None}")
            
            if not payment:
                # Payment bulunamadi
                frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'
                error_msg = f"Payment bulunamadi. Conversation ID: {conversation_id}, Basket ID: {basket_id}"
                logger.error(error_msg)
                redirect_url = f"{frontend_url}/payment/callback?token={token}&status=error&error={error_msg}"
                return HttpResponseRedirect(redirect_url)
            
            try:
                logger.info(f"Payment bulundu - ID: {payment.id}, Appointment ID: {payment.appointment.id}")
                
                # Odeme basarili
                payment.status = 'completed'
                payment.iyzico_payment_id = result.get('payment_id')
                payment.payment_method = 'card'
                payment.paid_at = timezone.now()
                payment.save()
                logger.info(f"Payment guncellendi - Status: {payment.status}")
                
                # Randevu status'unu 'paid' olarak guncelle
                appointment = payment.appointment
                appointment.status = 'paid'
                appointment.save()
                logger.info(f"Appointment status guncellendi - ID: {appointment.id}, Status: {appointment.status}")
                
                # Ödeme tamamlandı email'i gönder
                try:
                    from appointments.email_service import send_payment_completed_email
                    send_payment_completed_email(payment)
                    logger.info(f"Ödeme tamamlanma email'i gönderildi - Payment ID: {payment.id}")
                except Exception as e:
                    logger.error(f"Ödeme tamamlanma email'i gönderilirken hata: {str(e)}", exc_info=True)
                    # Email hatası ödeme işlemini engellememeli
                
                # Basarili sayfasina redirect yap (payment/callback yerine patient-panel'e success parametresi ile)
                frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'
                redirect_url = f"{frontend_url}/patient-panel?payment_success=true&payment_id={payment.id}"
                logger.info(f"Frontend'e redirect yapiliyor: {redirect_url}")
                return HttpResponseRedirect(redirect_url)
            except Exception as e:
                # Payment veya appointment ile ilgili bir hata olustu
                error_msg = f"Payment veya appointment guncelleme hatasi: {str(e)}"
                logger.error(error_msg, exc_info=True)
                frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'
                redirect_url = f"{frontend_url}/payment/callback?token={token}&status=error&error={error_msg}"
                return HttpResponseRedirect(redirect_url)
        elif result['status'] == 'failed':
            # Odeme basarisiz - conversation_id'den payment'i bul
            conversation_id = result.get('conversation_id')
            if conversation_id:
                try:
                    payment = Payment.objects.get(iyzico_conversation_id=conversation_id)
                    payment.status = 'failed'
                    payment.error_message = result.get('error_message', 'Odeme basarisiz')
                    payment.save()
                except Payment.DoesNotExist:
                    pass
            
            # Frontend'e redirect yap (token ile, failed status ile)
            frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'
            redirect_url = f"{frontend_url}/payment/callback?token={token}&status=failed&error={result.get('error_message', 'Odeme basarisiz')}"
            return HttpResponseRedirect(redirect_url)
        elif result['status'] == 'error':
            # iyzico'dan hata geldi - conversation_id'den payment'i bul
            conversation_id = result.get('conversation_id')
            if conversation_id:
                try:
                    payment = Payment.objects.get(iyzico_conversation_id=conversation_id)
                    payment.status = 'failed'
                    payment.error_message = result.get('error_message', 'Odeme kontrol edilemedi')
                    payment.save()
                except Payment.DoesNotExist:
                    pass
            
            # Frontend'e redirect yap (token ile, error status ile)
            frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'
            redirect_url = f"{frontend_url}/payment/callback?token={token}&status=error&error={result.get('error_message', 'Odeme kontrol edilemedi')}"
            return HttpResponseRedirect(redirect_url)
        else:
            # Beklenmeyen status degeri
            logger.warning(f"Beklenmeyen iyzico status degeri (callback): {result.get('status')}")
            conversation_id = result.get('conversation_id')
            if conversation_id:
                try:
                    payment = Payment.objects.get(iyzico_conversation_id=conversation_id)
                    payment.status = 'failed'
                    payment.error_message = f"Beklenmeyen durum: {result.get('status', 'bilinmiyor')}"
                    payment.save()
                except Payment.DoesNotExist:
                    pass
            
            # Frontend'e redirect yap
            frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'
            redirect_url = f"{frontend_url}/payment/callback?token={token}&status=error&error=Beklenmeyen durum"
            return HttpResponseRedirect(redirect_url)
            
    except Exception as e:
        logger.error(f"Callback hatasi: {str(e)}", exc_info=True)
        # Frontend'e hata ile redirect yap
        frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:5173'
        error_message = 'Callback islenirken bir hata olustu.'
        redirect_url = f"{frontend_url}/payment/callback?status=error&error={error_message}"
        return HttpResponseRedirect(redirect_url)