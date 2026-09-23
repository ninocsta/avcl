from django.test import TestCase


class HealthTests(TestCase):
    def test_health_ok_sem_login(self):
        self.assertEqual(self.client.get("/health/").status_code, 200)
