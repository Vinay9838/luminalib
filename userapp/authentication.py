from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

from .auth_service import AuthService

class TokenAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth = request.headers.get('x-jwt-assertion')
        if not auth:
            return None
        auth_service = AuthService()
        user = auth_service.get_user(auth)
        if not user:
            raise exceptions.AuthenticationFailed('Invalid or expired token')
        return (user, auth)