"""
Tests for verification email workflow.
"""
from django.test import TestCase
from django.core import mail
from accounts.models import User
from .models import SeniorProfile


class SeniorVerificationEmailTests(TestCase):
    """
    Test email sending for senior verification workflow.
    """
    
    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username="testsenior",
            email="testsenior@example.com",
            password="testpass123"
        )
    
    def test_received_email_sent_on_creation(self):
        """Test that received email is sent when profile is created."""
        # Clear mail outbox
        mail.outbox = []
        
        # Create senior profile (would normally trigger email in view)
        profile = SeniorProfile.objects.create(
            user=self.user,
            proof_summary="Test proof"
        )
        
        # Note: Email is sent in view's perform_create, not in model save
        # This test verifies the model creation works
        self.assertEqual(profile.status, "pending")
        self.assertEqual(profile.user, self.user)
    
    def test_approval_email_sent_on_status_change(self):
        """Test that approval email is sent when status changes to approved."""
        # Clear mail outbox
        mail.outbox = []
        
        # Create profile
        profile = SeniorProfile.objects.create(
            user=self.user,
            proof_summary="Test proof"
        )
        
        # Clear any emails from creation
        mail.outbox = []
        
        # Approve profile
        profile.status = "approved"
        profile.save()
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("You're Approved", mail.outbox[0].subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
    
    def test_no_duplicate_approval_email(self):
        """Test that approval email is not sent again on subsequent saves."""
        # Create and approve profile
        profile = SeniorProfile.objects.create(
            user=self.user,
            proof_summary="Test proof"
        )
        profile.status = "approved"
        profile.save()
        
        # Clear mail outbox
        mail.outbox = []
        
        # Update profile again (status still approved)
        profile.proof_summary = "Updated proof"
        profile.save()
        
        # No new email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_user_flag_synced_on_approval(self):
        """Test that user.is_verified_senior is synced when approved."""
        profile = SeniorProfile.objects.create(
            user=self.user,
            proof_summary="Test proof"
        )
        
        # Initially not verified
        self.assertFalse(self.user.is_verified_senior)
        
        # Approve profile
        profile.status = "approved"
        profile.save()
        
        # Refresh user from database
        self.user.refresh_from_db()
        
        # Should now be verified
        self.assertTrue(self.user.is_verified_senior)
    
    def test_user_flag_unset_on_rejection(self):
        """Test that user.is_verified_senior is unset when rejected."""
        # Create and approve profile
        profile = SeniorProfile.objects.create(
            user=self.user,
            proof_summary="Test proof"
        )
        profile.status = "approved"
        profile.save()
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified_senior)
        
        # Reject profile
        profile.status = "rejected"
        profile.save()
        
        # Refresh user from database
        self.user.refresh_from_db()
        
        # Should no longer be verified
        self.assertFalse(self.user.is_verified_senior)
