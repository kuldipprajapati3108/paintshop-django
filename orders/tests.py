from django.test import TestCase, override_settings
from django.core import mail
from unittest.mock import patch, MagicMock
from orders.email_utils import (
    send_email_notification,
    send_order_confirmation_email,
    send_order_status_update_email,
    send_delivery_update_email,
    send_new_order_notification_to_admin
)
from orders.models import Order, OrderItem, Payment
from accounts.models import Customer
from staff.models import Staff


class EmailUtilsTestCase(TestCase):
    """Test email utility functions."""

    def setUp(self):
        """Set up test data."""
        self.customer = Customer.objects.create(
            email='test@example.com',
            name='Test User'
        )
        self.order = Order.objects.create(
            customer=self.customer,
            total_amount=100.00,
            status='pending'
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product_id=1,
            quantity=1,
            price=100.00
        )

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_send_order_confirmation_email(self):
        """Test order confirmation email."""
        result = send_order_confirmation_email(self.order, self.customer)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Order Confirmation - Order #{self.order.order_id} - Shree Shankar Traders')
        self.assertEqual(mail.outbox[0].to, [self.customer.email])

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_send_order_status_update_email(self):
        """Test order status update email."""
        self.order.status = 'confirmed'
        result = send_order_status_update_email(self.order, self.customer)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Status Update', mail.outbox[0].subject)

    def test_send_email_notification_with_invalid_template(self):
        """Test email with invalid template."""
        result = send_email_notification(
            subject='Test',
            template_name='invalid_template.html',
            context={},
            recipient_list=['test@example.com']
        )
        self.assertFalse(result)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        ADMIN_EMAIL='admin@example.com'
    )
    def test_send_new_order_notification_to_admin(self):
        """Test admin notification."""
        # Create a superuser with email
        from django.contrib.auth.models import User
        User.objects.create_superuser(
            username='admin',
            email='superadmin@example.com',
            password='admin123'
        )

        result = send_new_order_notification_to_admin(self.order, self.customer)

        self.assertTrue(result)
        # Should send to both superuser and ADMIN_EMAIL setting
        self.assertGreaterEqual(len(mail.outbox), 1)


class EmailConfigurationTestCase(TestCase):
    """Test email configuration."""

    def test_email_settings_configured(self):
        """Check if email settings are properly configured."""
        from django.conf import settings

        # These should be set in production
        if not settings.DEBUG:
            self.assertNotEqual(settings.EMAIL_HOST_USER, '')
            self.assertNotEqual(settings.EMAIL_HOST_PASSWORD, '')
