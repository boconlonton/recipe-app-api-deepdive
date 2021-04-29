from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Latte',
        'time_minutes': 10,
        'price': 5.5
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test the public Recipe APIs"""

    def setUp(self):
        """Prepare for the tests"""
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for Recipe APIs"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test the authorized Recipe APIs"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@bocon.cloud',
            password='testPass',
            name='Test'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_recipes_success(self):
        """Test that retrieving list of recipes success"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_limited_recipe_for_authen_user_only(self):
        """Test that only retrieve recipes of authenticated user"""
        user2 = get_user_model().objects.create_user(
            email='test2@bocon.cloud',
            password='testPass2',
            name='Test2'
        )

        sample_recipe(user=self.user)
        sample_recipe(user=user2)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)
