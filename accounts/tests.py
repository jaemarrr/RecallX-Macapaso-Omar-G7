from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user('stu', 'stu@x.com', 'pass12345!', first_name='S', last_name='T')
        self.admin = User.objects.create_superuser('adm', 'adm@x.com', 'pass12345!')

    def test_register_validation_and_success(self):
        url = reverse('register')
        bad = self.client.post(url, {'username': 'n', 'first_name': 'A', 'last_name': 'B', 'email': 'stu@x.com',
                                     'password1': 'Str0ngPass!!', 'password2': 'Str0ngPass!!'})
        self.assertContains(bad, 'already exists')
        mismatch = self.client.post(url, {'username': 'n', 'first_name': 'A', 'last_name': 'B', 'email': 'n@x.com',
                                          'password1': 'Str0ngPass!!', 'password2': 'different'})
        self.assertEqual(User.objects.filter(username='n').count(), 0)
        ok = self.client.post(url, {'username': 'n', 'first_name': 'A', 'last_name': 'B', 'email': 'n@x.com',
                                    'password1': 'Str0ngPass!!', 'password2': 'Str0ngPass!!'})
        self.assertRedirects(ok, reverse('dashboard'), fetch_redirect_response=False)
        self.assertNotEqual(User.objects.get(username='n').password, 'Str0ngPass!!')

    def test_login_invalid_and_role_redirect(self):
        r = self.client.post(reverse('login'), {'username': 'stu', 'password': 'wrong'})
        self.assertContains(r, 'Invalid username or password')
        self.client.post(reverse('login'), {'username': 'adm', 'password': 'pass12345!'})
        self.assertRedirects(self.client.get(reverse('dashboard')), reverse('admin_dashboard'), fetch_redirect_response=False)

    def test_login_required_and_role_isolation(self):
        self.assertEqual(self.client.get(reverse('student_dashboard')).status_code, 302)
        self.client.login(username='stu', password='pass12345!')
        self.assertRedirects(self.client.get(reverse('admin_dashboard')), reverse('dashboard'), fetch_redirect_response=False)
        self.client.login(username='adm', password='pass12345!')
        self.assertRedirects(self.client.get(reverse('student_dashboard')), reverse('dashboard'), fetch_redirect_response=False)

    def test_profile_update_and_logout(self):
        self.client.login(username='stu', password='pass12345!')
        r = self.client.post(reverse('profile'), {'first_name': 'New', 'last_name': 'Name', 'email': 'stu@x.com', 'contact_number': '0917 123 4567'})
        self.assertRedirects(r, reverse('profile'))
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'New')
        self.client.post(reverse('logout'))
        self.assertEqual(self.client.get(reverse('profile')).status_code, 302)
