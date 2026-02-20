from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse

from userapp.serializers import SignupSerializer, SigninSerializer
from userapp.auth_service import AuthService


class SignupView(APIView):

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="User Signup",
        tags=["User"],
        description="Register a new user using email and password.",
        request=SignupSerializer,
        responses={
            201: OpenApiResponse(
                description="User registered successfully"
            ),
            400: OpenApiResponse(
                description="Validation error"
            ),
        },
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_service = AuthService()
        auth_service.signup(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        return Response(
            {"message": "User registered successfully"},
            status=status.HTTP_201_CREATED,
        )
    

class SigninView(APIView):

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="User Signin",
        tags=["User"],
        description="Authenticate user and return JWT token.",
        request=SigninSerializer,
        responses={
            200: OpenApiResponse(description="Signin successful"),
            400: OpenApiResponse(description="Invalid credentials"),
        },
    )
    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        auth_service = AuthService()
        result = auth_service.signin(
            email=user.email,
            password=request.data.get("password"),
        )

        return Response(
            {
                "access_token": result["access_token"],
                "expires_in": 3600,
            },
            status=status.HTTP_200_OK,
        )
