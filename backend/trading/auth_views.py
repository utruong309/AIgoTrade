from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db import transaction
from decimal import Decimal

from .models import User, Portfolio
from .serializers import UserRegistrationSerializer, UserProfileSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                user = serializer.save()
                token, created = Token.objects.get_or_create(user=user)
                initial_cash = request.data.get('initial_cash', 0)
                if initial_cash and float(initial_cash) > 0:
                    default_portfolio = Portfolio.objects.get(user=user, is_default=True)
                    default_portfolio.cash_balance = Decimal(str(initial_cash))
                    default_portfolio.save()
                return Response({
                    'success': True,
                    'message': 'User registered successfully',
                    'user': UserProfileSerializer(user).data,
                    'token': token.key
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    if not email or not password:
        return Response({
            'success': False,
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(username=email, password=password)
    if user is not None:
        if user.is_active:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'success': True,
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Account is disabled'
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({
            'success': False,
            'error': 'Invalid email or password'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout(request):
    try:
        request.user.auth_token.delete()
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def profile(request):
    if request.user.is_authenticated:
        return Response({
            'success': True,
            'user': UserProfileSerializer(request.user).data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'error': 'Authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)