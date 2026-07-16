from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Department, Status, Document

class SmartFlowTestCase(TestCase):
    def setUp(self):
        # Create dependencies for tests
        self.dept = Department.objects.create(dept_name="Registry")
        self.clerk = User.objects.create_user(username='clerk1', password='password', role='clerk', dept=self.dept)
        self.status = Status.objects.create(status_name="Pending", status_code="PENDING")
        
        self.client = Client()
        self.client.login(username='clerk1', password='password')

    def test_document_registration(self):
        """Test that a clerk can successfully register a document."""
        response = self.client.post(reverse('register_document'), {
            'title': 'New Test Document',
            'description': 'Test Description',
            'document_type': 'Letter',
            'dept': self.dept.id,
            'requires_approval': True
        })
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        # Verify document creation
        self.assertEqual(Document.objects.count(), 1)
        self.assertEqual(Document.objects.first().status.status_code, 'PENDING')

    def test_unauthorized_access(self):
        """Test that non-admin users cannot access the audit trail."""
        self.client.logout()
        self.client.login(username='clerk1', password='password')
        response = self.client.get(reverse('audit_trail'))
        
        # Should be redirected to dashboard or login
        self.assertNotEqual(response.status_code, 200)
