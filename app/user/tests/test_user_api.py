from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """Create user helper function """
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test publicly available user APIs"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test create user with valid payload is successful"""
        payload = {
            'email': 'test@bocon.cloud',
            'password': 'testPass',
            'name': 'Test'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(
            email=payload['email']
        )
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test create user that already exists fails"""
        payload = {
            'email': 'test@bocon.cloud',
            'password': 'testPass'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that password must be more than 5 characters"""
        payload = {
            'email': 'test@bocon.cloud',
            'password': 'pw'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that create token successfully"""
        payload = {
            'email': "test@bocon.cloud",
            'password': 'testPass',
            'name': 'Test'
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created if invalid credentials"""
        payload = {
            'email': 'test@bocon.cloud',
            'password': 'ttttttt'
        }
        create_user(
            email='test@bocon.cloud',
            password='testPass'
        )
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_no_user(self):
        """Test that token is not created with non exists user"""
        payload = {
            'email': 'test@bocon.cloud',
            'password': 'testPass'
        }
        user_exist = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exist)

        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_without_password(self):
        """Test that token is not created if no password"""
        payload = {
            'email': 'test@bocon.cloud',
            'password': ''
        }
        create_user(
            email='test@bocon.cloud',
            password='testPass'
        )

        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_retrieve_user_unauthorized(self):
        """Test that retrieve a user without token"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test privately available user APIs"""

    def setUp(self):
        self.user = create_user(
            email='test@bocon.cloud',
            password='testPass',
            name='Name',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name
        })

    def test_post_not_allowed(self):
        """Test that POST is not allowed in the me url"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test that updating user profile for authenticated user"""
        payload = {
            'name': 'new name',
            'password': 'newPassword'
        }

        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
