from django.test import TestCase
from rest_framework.test import APIClient
from .models import User, Donation, FoodItem

class DonationAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.food_item = FoodItem.objects.create(name='Test Food', quantity=10)

    def test_create_donation(self):
        data = {'food_item': self.food_item.id, 'quantity': 5}
        response = self.client.post('/api/v1/donations/', data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Donation.objects.count(), 1)
        self.assertEqual(Donation.objects.get().quantity, 5)

# Add more test cases for other endpoints and scenarios