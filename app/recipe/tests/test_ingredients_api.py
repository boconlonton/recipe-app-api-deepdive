from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe import serializers


INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTests(TestCase):
    """Test for public Ingredient APIs"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for Ingredient APIs"""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test for authorized Ingredient APIs"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@bocon.cloud',
            password='testPass',
            name='Test'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients_success(self):
        """Test that retrieving list of ingredients successfully"""
        Ingredient.objects.create(
            name='Ginger',
            user=self.user
        )
        Ingredient.objects.create(
            name='Vinegar',
            user=self.user
        )

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer_obj = serializers.IngredientSerializer(
            ingredients,
            many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer_obj.data)

    def test_limited_ingredients(self):
        """Test that retrieving ingredients of authenticated user only"""
        user2 = get_user_model().objects.create_user(
            email='test2@bocon.cloud',
            password='testPass2',
            name='Test2'
        )
        ingred1 = Ingredient.objects.create(
            name='Ginger',
            user=self.user
        )
        Ingredient.objects.create(
            name='SoySauce',
            user=user2
        )

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingred1.name)
