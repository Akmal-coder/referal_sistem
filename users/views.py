from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .models import User
from .services import send_verification_code
from .serializers import (
    SendCodeSerializer,
    VerifyCodeSerializer,
    ActivateInviteSerializer,
    UserProfileSerializer,
)


@api_view(['POST'])
def send_code(request):
    """Отправка кода верификации на номер телефона."""
    serializer = SendCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data['phone_number']

    user, _ = User.objects.get_or_create(phone_number=phone)
    code = send_verification_code(phone)
    user.verification_code = code
    user.save()

    return Response({'message': f'Код отправлен на {phone}'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def verify_code(request):
    """Проверка кода и выдача JWT токенов."""
    serializer = VerifyCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data['phone_number']
    code = serializer.validated_data['code']

    try:
        user = User.objects.get(phone_number=phone)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    if user.verification_code != code:
        return Response({'error': 'Неверный код'}, status=status.HTTP_400_BAD_REQUEST)

    user.is_verified = True
    user.verification_code = None
    user.save()

    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Профиль текущего пользователя."""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_invite(request):
    """Активация чужого инвайт-кода."""
    serializer = ActivateInviteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    code = serializer.validated_data['invite_code']

    user = request.user

    if user.activated_invite_code:
        return Response({'error': 'Инвайт-код уже активирован'}, status=status.HTTP_400_BAD_REQUEST)

    if code == user.invite_code:
        return Response({'error': 'Нельзя активировать свой инвайт-код'}, status=status.HTTP_400_BAD_REQUEST)

    if not User.objects.filter(invite_code=code).exists():
        return Response({'error': 'Инвайт-код не найден'}, status=status.HTTP_404_NOT_FOUND)

    user.activated_invite_code = code
    user.save()

    return Response({'message': f'Инвайт-код {code} активирован'})


@login_required
def profile_page(request):
    """Страница профиля."""
    user = request.user
    referrals = User.objects.filter(activated_invite_code=user.invite_code)

    message = None
    error = None
    if request.method == 'POST':
        invite_code = request.POST.get('invite_code')
        if user.activated_invite_code:
            error = 'Инвайт-код уже активирован'
        elif invite_code == user.invite_code:
            error = 'Нельзя активировать свой инвайт-код'
        elif not User.objects.filter(invite_code=invite_code).exists():
            error = 'Инвайт-код не найден'
        else:
            user.activated_invite_code = invite_code
            user.save()
            message = f'Инвайт-код {invite_code} активирован'

    return render(request, 'users/profile.html', {
        'user': user,
        'referrals': referrals,
        'message': message or error,
    })


def auth_page(request):
    """Страница авторизации."""
    if request.user.is_authenticated:
        return redirect('profile-page')

    phone = ''
    error = None
    code_sent = False

    if request.method == 'POST':
        action = request.POST.get('action')
        phone = request.POST.get('phone_number')

        if action == 'send_code':
            try:
                from .services import send_verification_code
                user, _ = User.objects.get_or_create(phone_number=phone)
                code = send_verification_code(phone)
                user.verification_code = code
                user.save()
                code_sent = True
            except Exception as e:
                error = str(e)

        elif action == 'verify_code':
            code = request.POST.get('code')
            try:
                user = User.objects.get(phone_number=phone)
                if user.verification_code == code:
                    user.is_verified = True
                    user.verification_code = None
                    user.save()
                    login(request, user)
                    return redirect('profile-page')
                else:
                    error = 'Неверный код'
            except User.DoesNotExist:
                error = 'Пользователь не найден'

    return render(request, 'users/auth.html', {
        'phone': phone,
        'error': error,
        'code_sent': code_sent,
    })


def logout_view(request):
    """Выход из аккаунта."""
    logout(request)
    return redirect('auth-page')