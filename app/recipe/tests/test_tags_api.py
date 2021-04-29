from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag

from recipe.serializers import TagSerializer

TAG_URL = reverse('recipe:tag-list')


class PublicApiTests(TestCase):
    """Test the publicly available Tag APIs"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test login is required for retrieving tags"""
        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateApiTests(TestCase):
    """Test the authorized Tag APIs"""

    def setUp(self):
        """Before testing"""
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@bocon.cloud',
            password='TestPass',
            name='Testing'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """Test that retrieving tags is successful"""
        Tag.objects.create(
            name='Vegan',
            user=self.user
        )
        Tag.objects.create(
            name='Dessert',
            user=self.user
        )

        res = self.client.get(TAG_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for authenticated user"""
        user_test = get_user_model().objects.create_user(
            email='test2@bocon.cloud',
            password='testPass2',
            name='Test2'
        )
        tag = Tag.objects.create(
            name='Vegan',
            user=self.user
        )
        Tag.objects.create(
            name='Dessert',
            user=user_test
        )

        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
