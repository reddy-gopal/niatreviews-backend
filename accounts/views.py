from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

from .serializers import ProfileSerializer, PublicProfileSerializer, SeniorsSetupSerializer

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        if not username or not email or not password:
            return Response(
                {"detail": "username, email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {"username": "A user with that username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(email=email).exists():
            return Response(
                {"email": "A user with that email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.create_user(username=username, email=email, password=password)
        return Response(
            {"id": str(user.id), "username": user.username, "email": user.email},
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    """GET and PATCH current user profile. Requires authentication."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        data = dict(serializer.data)
        data["needs_password_set"] = not request.user.has_usable_password()
        return Response(data)

    def patch(self, request):
        user = request.user
        # First-time setup: allow setting username and password when no usable password
        if not user.has_usable_password():
            setup = SeniorsSetupSerializer(data=request.data, context={"user": user})
            if setup.is_valid():
                if setup.validated_data.get("username"):
                    user.username = setup.validated_data["username"].strip()
                user.set_password(setup.validated_data["password"])
                user.save(update_fields=["username", "password"])
                return Response(ProfileSerializer(user).data)
            return Response(setup.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)


class UserProfileByUsernameView(APIView):
    """GET: public profile by username for /api/users/<username>/."""
    permission_classes = [AllowAny]

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({"code": "NOT_FOUND", "detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PublicProfileSerializer(user, context={"request": request})
        return Response(serializer.data)
