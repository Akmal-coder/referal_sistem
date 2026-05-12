from django.test import TestCase, Client
from django.urls import reverse
from users.models import User


class UserModelTest(TestCase):
    """Тесты модели User."""

    def test_create_user(self):
        user = User.objects.create_user(phone_number='+79991112233')
        self.assertEqual(user.phone_number, '+79991112233')
        self.assertEqual(len(user.invite_code), 6)
        self.assertFalse(user.is_verified)

    def test_invite_code_unique(self):
        user1 = User.objects.create_user(phone_number='+79991112233')
        user2 = User.objects.create_user(phone_number='+79991112244')
        self.assertNotEqual(user1.invite_code, user2.invite_code)


class AuthAPITest(TestCase):
    """Тесты API авторизации."""

    def setUp(self):
        self.client = Client()
        self.send_code_url = reverse('api-send-code')
        self.verify_code_url = reverse('api-verify-code')

    def test_send_code_creates_user(self):
        response = self.client.post(self.send_code_url,
            {'phone_number': '+79991112233'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(phone_number='+79991112233').exists())

    def test_send_code_existing_user(self):
        User.objects.create_user(phone_number='+79991112233')
        response = self.client.post(self.send_code_url,
            {'phone_number': '+79991112233'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_verify_code_wrong(self):
        User.objects.create_user(phone_number='+79991112233', verification_code='1234')
        response = self.client.post(self.verify_code_url,
            {'phone_number': '+79991112233', 'code': '0000'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_verify_code_correct(self):
        User.objects.create_user(phone_number='+79991112233', verification_code='1234')
        response = self.client.post(self.verify_code_url,
            {'phone_number': '+79991112233', 'code': '1234'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())


class ProfileAPITest(TestCase):
    """Тесты API профиля."""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(phone_number='+79991112233')
        # Имитируем верификацию и логин
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)
        self.profile_url = reverse('api-profile')
        self.activate_url = reverse('api-activate-invite')

    def test_profile_authenticated(self):
        response = self.client.get(self.profile_url,
            HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['phone_number'], '+79991112233')
        self.assertEqual(len(data['invite_code']), 6)

    def test_profile_unauthorized(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 401)

    def test_activate_invite_code(self):
        user2 = User.objects.create_user(phone_number='+79991112244')
        response = self.client.post(self.activate_url,
            {'invite_code': user2.invite_code},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.activated_invite_code, user2.invite_code)

    def test_activate_own_invite_code(self):
        response = self.client.post(self.activate_url,
            {'invite_code': self.user1.invite_code},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 400)

    def test_activate_invite_code_twice(self):
        user2 = User.objects.create_user(phone_number='+79991112244')
        self.user1.activated_invite_code = user2.invite_code
        self.user1.save()
        user3 = User.objects.create_user(phone_number='+79991112255')
        response = self.client.post(self.activate_url,
            {'invite_code': user3.invite_code},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 400)

    def test_referrals_list(self):
        user2 = User.objects.create_user(phone_number='+79991112244')
        user2.activated_invite_code = self.user1.invite_code
        user2.save()
        response = self.client.get(self.profile_url,
            HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = response.json()
        self.assertIn('+79991112244', data['referrals'])


class TemplateViewTest(TestCase):
    """Тесты Django Template страниц."""

    def setUp(self):
        self.client = Client()
        self.auth_page_url = reverse('auth-page')

    def test_auth_page_get(self):
        response = self.client.get(self.auth_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Авторизация по номеру телефона')

    def test_auth_send_code(self):
        response = self.client.post(self.auth_page_url,
            {'phone_number': '+79991112233', 'action': 'send_code'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(phone_number='+79991112233').exists())
        self.assertContains(response, 'Введите код из SMS')

    def test_auth_verify_code_and_login(self):
        user = User.objects.create_user(phone_number='+79991112233', verification_code='1234')
        response = self.client.post(self.auth_page_url,
            {'phone_number': '+79991112233', 'code': '1234', 'action': 'verify_code'})
        self.assertRedirects(response, reverse('profile-page'))

    def test_profile_page_authenticated(self):
        user = User.objects.create_user(phone_number='+79991112233')
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        self.client.force_login(user)
        response = self.client.get(reverse('profile-page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, user.phone_number)
