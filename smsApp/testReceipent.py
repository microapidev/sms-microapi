from django.test import TestCase
from smsApp.models import Receipent

# Create your tests here.

class ReceipentTestCase(TestCase):
    def testReceipent(self):
        receipent = Receipent(id="id", name="name", email="email", phone_number="phone_number")
        self.assertEqual(receipent.id, "id")
        self.assertEqual(receipent.name, "name")
        self.assertEqual(receipent.email, "email")
        self.assertEqual(receipent.phone_number, "phone_number")