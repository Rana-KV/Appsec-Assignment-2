from django.test import TestCase
from LegacySite.models import Card

# Create your tests here.

class MyTest(TestCase):
    # Django's test run with an empty database. We can populate it with
    # data by using a fixture. You can create the fixture by running:
    #    mkdir LegacySite/fixtures
    #    python manage.py dumpdata LegacySite > LegacySite/fixtures/testdata.json
    # You can read more about fixtures here:
    #    https://docs.djangoproject.com/en/4.0/topics/testing/tools/#fixture-loading
    fixtures = ["testdata.json"]

    # Assuming that your database had at least one Card in it, this
    # test should pass.    
    def test_get_card(self):
        allcards = Card.objects.all()
        self.assertNotEqual(len(allcards), 0)
   
    def test_visit_website_no_alert(self):
        response = self.client.get('http://localhost:8000/buy/1?director=<script>alert("hello")</script>')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'alert("hello")')
        
    def test_csrf_token(self):
        self.client.login(username='testuser', password='test')
        '''
        # Make a POST request without a CSRF token
        response = self.client.post('http://localhost:8000/gift/1', {'username': 'testuser2', 'amount': ''}, secure=True)
        self.assertEqual(response.status_code, 403)
        '''
        # Make a POST request with an invalid CSRF token
        response = self.client.post('http://localhost:8000/gift/1', {'username': 'test2', 'amount': ''}, secure=True, HTTP_X_CSRFTOKEN='invalid_token')
        self.assertEqual(response.status_code, 403)
