from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse


class HomeViewTests(TestCase):

    def test_anonymous_gets_landing_page(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'home/landing.html')
        self.assertContains(resp, 'Entrar')

    def test_authenticated_redirects_to_character_home(self):
        user = User.objects.create_user(username='alice', password='pass')
        self.client.force_login(user)
        resp = self.client.get('/')
        self.assertRedirects(resp, reverse('character:home'), fetch_redirect_response=False)


class HealthCheckTest(TestCase):

    def test_healthz_returns_200_without_auth(self):
        resp = self.client.get('/healthz')
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(resp.content, {'ok': True})

    def test_healthz_rejects_post(self):
        resp = self.client.post('/healthz')
        self.assertEqual(resp.status_code, 405)
