import json
import tempfile

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from .models import User


class UserAdminTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser(username='admin', password='pass', email='admin@example.com')
        self.client = Client()
        self.client.force_login(self.staff)

    def test_user_list_accessible(self):
        url = reverse('users:user_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_user_create_update_and_delete(self):
        url = reverse('users:user_create')
        response = self.client.post(url, {
            'username': 'newuser',
            'password1': 'super-secret-pw1',
            'password2': 'super-secret-pw1',
            'email': 'new@example.com',
            'role': User.ROLE_MEMBER,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')

        update_url = reverse('users:user_update', args=[user.unique_id])
        response = self.client.post(update_url, {
            'first_name': 'New',
            'last_name': 'User',
            'email': 'changed@example.com',
            'role': User.ROLE_MEMBER,
            'preferred_language': 'fr',
        })
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.email, 'changed@example.com')

        detail_url = reverse('users:user_detail', args=[user.unique_id])
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'changed@example.com')

        delete_url = reverse('users:user_delete', args=[user.unique_id])
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_populate_users_command(self):
        data = [
            {'username': 'bob', 'email': 'bob@example.com', 'password': 'bobpw', 'is_staff': False}
        ]
        tmp = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
        json.dump(data, tmp)
        tmp.flush()
        tmp.close()
        call_command('populate_users', tmp.name)
        self.assertTrue(User.objects.filter(username='bob').exists())

    def test_login_and_signup_templates_used(self):
        anon_client = Client()

        login_url = reverse('account_login')
        resp = anon_client.get(login_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/login.html')

        signup_url = reverse('account_signup')
        resp = anon_client.get(signup_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/signup.html')

    def test_profile_page_renders(self):
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
