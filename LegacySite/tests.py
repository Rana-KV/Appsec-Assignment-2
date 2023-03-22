from django.test import TestCase, Client
from LegacySite.models import Card
import io

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
   
    def test_xss_alert(self):
        # Make a GET request with XSS payload
        response = self.client.get('http://localhost:8000/buy/1?director=<script>alert("hello")</script>')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'alert("hello")')
        
    def test_xsrf_POST(self):
        self.client = Client(enforce_csrf_checks=True)
        # Login has to be done before accessing gift page
        self.client.login(username='test', password='test')
        
        # Make a POST request without a CSRF token
        response = self.client.post('http://localhost:8000/gift/1', {'username': 'test2', 'amount': ''})
        self.assertEqual(response.status_code, 403)
        
    def test_SQLi_POST(self):
        self.client = Client()
        # Login has to be done before accessing gift page
        self.client.login(username='test', password='test')
        
        #POST Exploitable giftcard to web application
        with open('part-1/sqli.gftcrd', 'rb') as f:
                response = self.client.post('http://localhost:8000/use', {'card_data': f,'card_supplied':'True', 'card_fname':''})
                
                #The response code should be 200
                self.assertEqual(response.status_code, 200)
                
                #The web application should not leak the hashed password
                self.assertNotContains(response, '000000000000000000000000000078d2$18821d89de11ab18488fdc0a01f1ddf4d290e198b0f80cd4974fc031dc2615a3')
        
        with open('part-1/sqli2.gftcrd', 'rb') as f:
                response = self.client.post('http://localhost:8000/use', {'card_data': f,'card_supplied':'True', 'card_fname':''})
                
                #The response code should be 200
                self.assertEqual(response.status_code, 200)
                
                #The web application should not leak the hashed password
                self.assertNotContains(response, '000000000000000000000000000078d2$18821d89de11ab18488fdc0a01f1ddf4d290e198b0f80cd4974fc031dc2615a3')

    def test_Cmdi_POST(self):
        self.client = Client()
        # Login has to be done before accessing gift page
        self.client.login(username='test', password='test')
        with open('part-1/cmdi_exp.txt', 'rb') as f:
            response = self.client.post('http://localhost:8000/use', {'card_data': f,'card_supplied':'True', 'card_fname':'text | touch test.txt;'})
        try:
            with open('test.txt', 'rb') as f:
                 raise "Error"
        except:
            pass

    def test_buy_and_use(self):
            client = Client()
            client.login(username='test', password='test')
            response = client.post('/buy/2', {'amount': 100})
            self.assertEqual(response.status_code, 200)
            card_data = response.content
            response = client.post('/use.html',
                {
                    'card_supplied': 'True',
                    'card_fname': 'Test',
                    'card_data': io.BytesIO(card_data),
                }
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Card used!', response.content)