from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import SignupSerializer, LoginSerializer
from .models import User


def get_tokens_for_user(user):
    """
    Helper function — generates a JWT access + refresh token pair
    for a given user. Called after signup and login.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


class SignupView(APIView):
    """
    POST /api/auth/signup/
    Open to everyone — no authentication required.
    """

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user   = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Account created successfully.',
                'user': {
                    'id':       user.id,
                    'email':    user.email,
                    'username': user.username,
                    'role':     user.role,
                },
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Open to everyone — no authentication required.
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user   = serializer.validated_data['user']  
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Login successful.',
                'user': {
                    'id':       user.id,
                    'email':    user.email,
                    'username': user.username,
                    'role':     user.role,
                },
                'tokens': tokens
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Requires authentication — user must send their access token.
    Blacklists the refresh token so it can't be reused.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()   # invalidates the token in the DB
            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(APIView):
    """
    GET /api/auth/profile/
    Returns the currently logged-in user's details.
    # Good way to verify your token is working correctly.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user   # DRF automatically decodes token and attaches user
        return Response({
            'id':         user.id,
            'email':      user.email,
            'username':   user.username,
            'role':       user.role,
            'created_at': user.date_joined,
        })