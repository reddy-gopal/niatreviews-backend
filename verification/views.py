"""
Verification API views.
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SeniorProfile, PhoneVerification, SeniorRegistration
from .serializers import SeniorProfileSerializer, PhoneVerificationSerializer, SeniorRegistrationSerializer
from .services import send_senior_received_email, send_senior_registration_received_email


class SeniorProfileCreateAPIView(generics.CreateAPIView):
    """
    Create a senior verification request.
    Sends confirmation email immediately after creation.
    """
    queryset = SeniorProfile.objects.all()
    serializer_class = SeniorProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Create the senior profile and send confirmation email.
        """
        # Ensure user is set to the authenticated user
        profile = serializer.save(user=self.request.user)
        
        # Send "received" email immediately
        try:
            send_senior_received_email(profile.user)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send senior received email: {e}")


class SeniorProfileDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve senior profile details.
    """
    queryset = SeniorProfile.objects.all()
    serializer_class = SeniorProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """
        Return the senior profile for the authenticated user.
        """
        return SeniorProfile.objects.get(user=self.request.user)


class PhoneVerificationCreateAPIView(generics.CreateAPIView):
    """
    Create a phone verification request.
    """
    queryset = PhoneVerification.objects.all()
    serializer_class = PhoneVerificationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Create phone verification for authenticated user.
        """
        serializer.save(user=self.request.user)



class SeniorRegistrationCreateAPIView(generics.CreateAPIView):
    """
    Create a detailed senior registration from seniors-frontend.
    Sends confirmation email immediately after creation.
    No authentication required for initial registration.
    """
    queryset = SeniorRegistration.objects.all()
    serializer_class = SeniorRegistrationSerializer
    permission_classes = []  # Allow anonymous registration

    def perform_create(self, serializer):
        """
        Create the senior registration and send confirmation email.
        """
        registration = serializer.save()
        
        # Send "received" email immediately
        try:
            send_senior_registration_received_email(registration)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send senior registration received email: {e}")


class SeniorRegistrationListAPIView(generics.ListAPIView):
    """
    List all senior registrations (admin only).
    """
    queryset = SeniorRegistration.objects.all()
    serializer_class = SeniorRegistrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter by status if provided.
        """
        qs = super().get_queryset()
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs
