"""
iYZICO odeme servisi
"""
import iyzipay
from django.conf import settings
import logging
import json
from decimal import Decimal
from http.client import HTTPResponse

logger = logging.getLogger(__name__)


class IyzicoService:
    """
    iYZICO odeme islemleri icin servis sinifi
    """
    
    def __init__(self):
        self.api_key = settings.IYZICO_API_KEY
        self.secret_key = settings.IYZICO_SECRET_KEY
        # iyzico kutuphanesi sadece hostname istiyor, protokol olmadan
        base_url = settings.IYZICO_BASE_URL
        
        # Debug: Environment variable kontrolu
        if not self.api_key:
            logger.error("IYZICO_API_KEY environment variable bulunamadi!")
        else:
            logger.info(f"IYZICO_API_KEY yuklendi (ilk 10 karakter: {self.api_key[:10]}...)")
        
        if not self.secret_key:
            logger.error("IYZICO_SECRET_KEY (SANDBOX_SECRET_KEY) environment variable bulunamadi!")
        else:
            logger.info(f"IYZICO_SECRET_KEY yuklendi (ilk 10 karakter: {self.secret_key[:10]}...)")
        
        if not base_url:
            logger.error("IYZICO_BASE_URL environment variable bulunamadi!")
        else:
            logger.info(f"IYZICO_BASE_URL (ham): {base_url}")
        
        # URL'den protokolu kaldir (https:// veya http://)
        if base_url.startswith('https://'):
            self.base_url = base_url.replace('https://', '')
        elif base_url.startswith('http://'):
            self.base_url = base_url.replace('http://', '')
        else:
            self.base_url = base_url
        
        # Sandbox key kontrolu - eger sandbox key kullaniliyorsa sandbox URL'i zorla
        if self.api_key and 'sandbox' in self.api_key.lower():
            if 'api.iyzipay.com' in self.base_url.lower() and 'sandbox' not in self.base_url.lower():
                logger.warning(f"Sandbox API key kullaniliyor ama production URL ayarli! Sandbox URL'ine degistiriliyor...")
                logger.warning(f"Eski URL: {self.base_url}")
                self.base_url = 'sandbox-api.iyzipay.com'
                logger.info(f"Yeni URL: {self.base_url}")
        
        logger.info(f"IYZICO_BASE_URL (son): {self.base_url}")
        
        # iYZICO options
        self.options = {
            'api_key': self.api_key,
            'secret_key': self.secret_key,
            'base_url': self.base_url
        }
        
        # Eger API key veya secret key yoksa uyari ver
        if not self.api_key or not self.secret_key:
            logger.warning("iyzico API anahtarlari eksik! .env dosyasini kontrol edin.")
    
    def create_payment_request(self, payment_data):
        """
        Odeme istegi olusturur ve checkout form HTML'i dondurur
        payment_data icermeli:
        - conversation_id: Benzersiz konusma ID
        - price: Odeme tutari
        - paid_price: Odenecek tutar
        - basket_id: Sepet ID
        - buyer: Alici bilgileri (dict)
        - billing_address: Fatura adresi (dict)
        - shipping_address: Kargo adresi (dict - billing ile ayni olabilir)
        - basket_items: Sepet urunleri (list)
        """
        try:
            request = {
                'locale': 'tr',
                'conversationId': payment_data['conversation_id'],
                'price': str(payment_data['price']),
                'paidPrice': str(payment_data['paid_price']),
                'currency': payment_data.get('currency', 'TRY'),
                'basketId': payment_data['basket_id'],
                'paymentGroup': 'PRODUCT',
                'callbackUrl': payment_data.get('callback_url', ''),
                'enabledInstallments': payment_data.get('enabled_installments', []),
                'buyer': payment_data['buyer'],
                'shippingAddress': payment_data['shipping_address'],
                'billingAddress': payment_data['billing_address'],
                'basketItems': payment_data['basket_items']
            }
            
            checkout_form_initialize = iyzipay.CheckoutFormInitialize().create(request, self.options)
            
            # iyzico response'unun tipini kontrol et
            logger.info(f"iyzico response type: {type(checkout_form_initialize)}")
            
            # iyzico response'u dict olarak parse et
            response_data = None
            
            # Eger HTTPResponse ise icerigini oku
            if isinstance(checkout_form_initialize, HTTPResponse) or hasattr(checkout_form_initialize, 'read'):
                try:
                    if hasattr(checkout_form_initialize, 'read'):
                        content = checkout_form_initialize.read()
                        if content:
                            response_data = json.loads(content.decode('utf-8'))
                            logger.info(f"HTTPResponse'dan parse edilen data: {type(response_data)}, keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'N/A'}")
                except Exception as e:
                    logger.error(f"Response okuma hatasi: {str(e)}")
            
            # Eger dict degilse, dict benzeri obje olarak kullan
            if response_data is None:
                # Dict degilse, dict benzeri obje olarak kullan
                if isinstance(checkout_form_initialize, dict):
                    response_data = checkout_form_initialize
                    logger.info(f"Response zaten dict, keys: {list(response_data.keys())}")
                else:
                    # iyzico response'u genellikle bir dict benzeri obje dondurur
                    # Direkt attribute'lara erisebiliriz
                    response_data = checkout_form_initialize
                    logger.info(f"Response obje, attributes: {dir(response_data)[:10]}")
            
            # Status kontrolu
            status = None
            if isinstance(response_data, dict):
                status = response_data.get('status')
            else:
                status = getattr(response_data, 'status', None)
            
            if status == 'success':
                # Basarili yanit
                checkout_form_content = None
                payment_page_url = None
                
                if isinstance(response_data, dict):
                    # iyzico response'unda farkli anahtar isimleri olabilir
                    checkout_form_content = (
                        response_data.get('checkoutFormContent') or 
                        response_data.get('checkout_form_content') or
                        response_data.get('checkoutFormContent') or
                        response_data.get('content')
                    )
                    payment_page_url = (
                        response_data.get('paymentPageUrl') or 
                        response_data.get('payment_page_url') or
                        response_data.get('paymentPageUrl')
                    )
                    # Debug log
                    logger.info(f"iyzico response keys: {list(response_data.keys())}")
                    logger.info(f"checkout_form_content length: {len(checkout_form_content) if checkout_form_content else 0}")
                else:
                    checkout_form_content = (
                        getattr(response_data, 'checkoutFormContent', None) or 
                        getattr(response_data, 'checkout_form_content', None) or
                        getattr(response_data, 'content', None)
                    )
                    payment_page_url = (
                        getattr(response_data, 'paymentPageUrl', None) or 
                        getattr(response_data, 'payment_page_url', None)
                    )
                
                if not checkout_form_content:
                    logger.error(f"checkout_form_content bulunamadi! Response data: {str(response_data)[:500]}")
                    return {
                        'status': 'error',
                        'error_message': 'iyzico checkout form icerigi bulunamadi.'
                    }
                
                return {
                    'status': 'success',
                    'checkout_form_content': checkout_form_content,
                    'payment_page_url': payment_page_url
                }
            else:
                # Hata durumu - hata mesajini bul
                error_message = 'iYZICO odeme istegi basarisiz'
                error_code = None
                
                try:
                    if isinstance(response_data, dict):
                        error_message = response_data.get('errorMessage') or response_data.get('error_message') or error_message
                        error_code = response_data.get('errorCode') or response_data.get('error_code')
                    else:
                        error_message = getattr(response_data, 'errorMessage', None) or getattr(response_data, 'error_message', None) or error_message
                        error_code = getattr(response_data, 'errorCode', None) or getattr(response_data, 'error_code', None)
                    
                    if error_code:
                        error_message = f"{error_message} (Hata Kodu: {error_code})"
                    
                    # Full response'u logla (debug icin)
                    logger.error(f"iYZICO hatasi: {error_message}")
                    logger.debug(f"Full response type: {type(response_data)}, data: {str(response_data)[:500]}")
                        
                except Exception as e:
                    logger.error(f"Hata mesaji parse edilirken sorun: {str(e)}")
                    error_message = f"iYZICO odeme istegi basarisiz: {str(e)}"
                
                return {
                    'status': 'error',
                    'error_message': error_message
                }
                
        except Exception as e:
            logger.error(f"iYZICO odeme istegi olusturma hatasi: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error_message': str(e)
            }
    
    def retrieve_payment(self, token):
        """
        Odeme sonucunu token ile kontrol eder
        """
        try:
            request = {
                'locale': 'tr',
                'token': token
            }
            
            checkout_form_result = iyzipay.CheckoutForm().retrieve(request, self.options)
            
            # iyzico response'unu dict olarak parse et
            result_dict = {}
            
            # Eger HTTPResponse ise icerigini oku
            if isinstance(checkout_form_result, HTTPResponse) or hasattr(checkout_form_result, 'read'):
                try:
                    if hasattr(checkout_form_result, 'read'):
                        content = checkout_form_result.read()
                        if content:
                            # JSON string ise parse et
                            if isinstance(content, bytes):
                                content = content.decode('utf-8')
                            if isinstance(content, str):
                                result_dict = json.loads(content)
                            else:
                                result_dict = content if isinstance(content, dict) else {}
                            logger.info(f"Response parse edildi - Keys: {list(result_dict.keys())[:10]}")
                except Exception as e:
                    logger.error(f"Response parse hatasi: {str(e)}", exc_info=True)
                    # Attribute-based access'i dene
                    pass
            
            # Eger dict parse edilemediyse, response'un zaten dict olup olmadigini kontrol et
            if not result_dict:
                if isinstance(checkout_form_result, dict):
                    result_dict = checkout_form_result
                else:
                    # Response'un attribute'larini kontrol et
                    result_dict = {}
                    for attr in ['status', 'paymentStatus', 'payment_status', 'paymentId', 'payment_id', 
                                'conversationId', 'conversation_id', 'basketId', 'basket_id', 
                                'price', 'paidPrice', 'paid_price']:
                        if hasattr(checkout_form_result, attr):
                            value = getattr(checkout_form_result, attr)
                            # Camel case'i snake case'e cevir
                            key = attr.replace('Id', '_id').replace('Status', '_status').lower()
                            result_dict[key] = value
            
            logger.info(f"Parsed result_dict keys: {list(result_dict.keys())[:10]}")
            logger.info(f"Parsed result_dict status: {result_dict.get('status')}")
            
            # Response status'unu kontrol et
            status_value = result_dict.get('status') or (checkout_form_result.status if hasattr(checkout_form_result, 'status') else None)
            
            if status_value == 'success':
                # payment_status genellikle itemTransactions icinde veya direkt response'da olabilir
                payment_status = result_dict.get('paymentStatus') or result_dict.get('payment_status')
                
                # Eger payment_status yoksa, itemTransactions'dan kontrol et
                if not payment_status:
                    item_transactions = result_dict.get('itemTransactions', [])
                    if item_transactions and len(item_transactions) > 0:
                        payment_status = item_transactions[0].get('transactionStatus') or item_transactions[0].get('transaction_status')
                
                # Status success ise payment basarili sayilir
                return {
                    'status': 'success',
                    'payment_status': payment_status or 'SUCCESS',
                    'payment_id': result_dict.get('paymentId') or result_dict.get('payment_id'),
                    'conversation_id': result_dict.get('conversationId') or result_dict.get('conversation_id'),
                    'basket_id': result_dict.get('basketId') or result_dict.get('basket_id'),
                    'price': result_dict.get('price'),
                    'paid_price': result_dict.get('paidPrice') or result_dict.get('paid_price'),
                    'fraud_status': result_dict.get('fraudStatus') or result_dict.get('fraud_status'),
                    'installment': result_dict.get('installment')
                }
                
            else:
                error_message = 'Odeme kontrol hatasi'
                logger.error(f"iYZICO odeme kontrol hatasi: {error_message}")
                logger.error(f"iYZICO odeme kontrol hatasi: {error_message}")
                return {
                    'status': 'error',
                    'error_message': error_message
                }
                
        except Exception as e:
            logger.error(f"iYZICO odeme kontrol hatasi: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error_message': str(e)
            }
    
    def cancel_payment(self, payment_id, ip_address, price=None):
        """
        Odemeyi iptal eder (iade)
        """
        try:
            request = {
                'locale': 'tr',
                'paymentId': payment_id,
                'ip': ip_address
            }
            
            if price:
                request['price'] = str(price)
            
            cancel = iyzipay.Cancel().create(request, self.options)
            
            if hasattr(cancel, 'status') and cancel.status == 'success':
                return {
                    'status': 'success',
                    'payment_id': getattr(cancel, 'payment_id', None)
                }
            else:
                # Hata mesajini guvenli sekilde al
                error_message = 'Odeme iptal hatasi'
                try:
                    if hasattr(cancel, 'error_message'):
                        error_message = cancel.error_message
                    elif hasattr(cancel, 'read'):
                        content = cancel.read()
                        if content:
                            import json
                            try:
                                error_data = json.loads(content.decode('utf-8'))
                                error_message = error_data.get('errorMessage', error_data.get('error_message', str(content)))
                            except:
                                error_message = f"iYZICO hatasi: {str(content[:200])}"
                    else:
                        error_message = f"iYZICO hatasi: {str(cancel)}"
                except Exception as e:
                    logger.error(f"Hata mesaji okunurken sorun: {str(e)}")
                
                logger.error(f"iYZICO odeme iptal hatasi: {error_message}")
                return {
                    'status': 'error',
                    'error_message': error_message
                }
                
        except Exception as e:
            logger.error(f"iYZICO odeme iptal hatasi: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error_message': str(e)
            }
