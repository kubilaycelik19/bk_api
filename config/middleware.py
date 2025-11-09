"""
Custom middleware for debugging API requests
"""
import logging

logger = logging.getLogger(__name__)

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Sadece API endpoint'lerine gelen istekleri logla
        if request.path.startswith('/api/'):
            print(f"🌐 [MIDDLEWARE] İstek geldi: {request.method} {request.path}")
            print(f"🌐 [MIDDLEWARE] User: {request.user.email if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'}")
            auth_header = request.headers.get('Authorization', 'Yok')
            if auth_header and auth_header.startswith('Bearer '):
                print(f"🌐 [MIDDLEWARE] Authorization: Bearer *** (Token var)")
            else:
                print(f"🌐 [MIDDLEWARE] Authorization: Yok")
            logger.info(f"🌐 [MIDDLEWARE] İstek: {request.method} {request.path}")
        
        response = self.get_response(request)
        
        if request.path.startswith('/api/'):
            print(f"🌐 [MIDDLEWARE] Response: {response.status_code}")
            logger.info(f"🌐 [MIDDLEWARE] Response: {response.status_code}")
        
        return response

