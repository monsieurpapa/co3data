from django.test import TestCase, Client
from django.urls import reverse
from .models import User
from django.core.management import call_command
import tempfile
import json

class UserAdminTests(TestCase):
    def setUp(self):
        # use superuser for admin management RBAC
        self.staff = User.objects.create_superuser(username='admin', password='pass', email='admin@example.com')
        self.client = Client()
        self.client.force_login(self.staff)

    def test_user_list_accessible(self):
        url = reverse('users:user_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_user_create_update_and_delete(self):
        # need an organization to assign
        from organization.models import Organization
        org = Organization.objects.create(name='Org1', unique_code='ORG1')

        # create a user
        url = reverse('users:user_add')
        response = self.client.post(url, {
            'username': 'newuser',
            'password': 'secret',
            'email': 'new@example.com',
            'organization': org.pk,
            'role': '',
        })
        # after creation should redirect to list
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')

        # update via view
        update_url = reverse('users:user_edit', args=[user.unique_id])
        response = self.client.post(update_url, {
            'username': 'newuser',
            'password': 'secret',
            'email': 'changed@example.com',
            'organization': org.pk,
            'role': '',
        })
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.email, 'changed@example.com')

        # detail view should show the updated email
        detail_url = reverse('users:user_detail', args=[user.unique_id])
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'changed@example.com')

        # delete via view
        delurl = reverse('users:user_delete', args=[user.unique_id])
        response = self.client.post(delurl)
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

    def test_navbar_contains_admin_links_for_staff(self):
        # load dashboard (any authenticated view with nav)
        url = reverse('accounting:dashboard')
        response = self.client.get(url)
        self.assertContains(response, reverse('users:user_list'))
        self.assertContains(response, reverse('organization:organization_list'))

    def test_login_and_signup_templates_used(self):
        # Create an anonymous client to test authentication pages
        anon_client = Client()
        
        # Test that allauth login template is rendered correctly
        login_url = reverse('account_login')
        resp = anon_client.get(login_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/login.html')
        self.assertContains(resp, 'Sign In')

        # Test that allauth signup template is rendered correctly
        signup_url = reverse('account_signup')
        resp = anon_client.get(signup_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account/signup.html')
        self.assertContains(resp, 'Sign Up')

    def test_profile_page_renders(self):
        # authenticated user should be able to view their profile without errors
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')