import os
from datetime import timedelta, datetime, UTC

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

from userapp.utils.jwt import BaseJWTValidator

User = get_user_model()



class JWTAuthValidator(BaseJWTValidator):

    required_claims_mapping = {
        'email': 'email',
    }

class TokenService:

    def __init__(self):
        self.jwt_validator = JWTAuthValidator(settings.BACKEND_JWT_SECRET, verify_exp=False)

    def validate_token(self, token: str) -> dict | None:
        return self.jwt_validator(token)
    
    def create_token(self, **token_data):
        return self.jwt_validator.encode_token(
            exp=datetime.now(UTC) + timedelta(hours=1),
            **token_data
        )
    

class AuthService:

    def __init__(self):
        self.token_service = TokenService()

    def get_user(self, jwt_token: str):
        if not jwt_token:
            return None

        user_data = self.token_service.validate_token(jwt_token)
        if not user_data:
            return None

        email = user_data.get("email")
        if not email:
            return None

        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        
    def signup(self, email: str, password: str):
        user = User(email=email)
        user.set_password(password)  # hash password properly
        user.save()
        return user
    
    def signin(self, email: str, password: str):
        user = authenticate(username=email, password=password)
        if not user:
            return None

        token = self.token_service.create_token(
            email=user.email
        )

        return {
            "user": user,
            "access_token": token,
        }
