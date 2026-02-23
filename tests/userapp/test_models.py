from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for custom User model"""

    def test_user_creation_with_email(self):
        """Test creating a user with email"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.assertEqual(user.email, "test@example.com")

    def test_user_password_is_hashed(self):
        """Test that user password is hashed"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        # Password should not be stored in plain text
        self.assertNotEqual(user.password, "testpass123")

    def test_user_email_is_unique(self):
        """Test that email field is unique"""
        User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="test@example.com",
                password="otherpass123"
            )

    def test_user_check_password(self):
        """Test checking user password"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.check_password("wrongpass"))

    def test_user_username_field_is_email(self):
        """Test that USERNAME_FIELD is email"""
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_user_no_username_field(self):
        """Test that username field is None"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.assertIsNone(user.username)

    def test_user_is_staff_default_false(self):
        """Test that is_staff defaults to False"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.assertFalse(user.is_staff)

    def test_user_is_active_default_true(self):
        """Test that is_active defaults to True"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.assertTrue(user.is_active)

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_str_representation(self):
        """Test string representation of user"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        # Typically returns email or first_name + last_name
        str_repr = str(user)
        self.assertIsNotNone(str_repr)

    def test_user_update(self):
        """Test updating user data"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        user.first_name = "John"
        user.last_name = "Doe"
        user.save()
        
        refreshed_user = User.objects.get(email="test@example.com")
        self.assertEqual(refreshed_user.first_name, "John")
        self.assertEqual(refreshed_user.last_name, "Doe")
