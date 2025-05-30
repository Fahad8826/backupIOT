# views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

# views.py

from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate


User = get_user_model()



ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


class AdminLoginView(APIView):
    permission_classes = [AllowAny]  # Important! Allow anyone to access this endpoint

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        # Log the login attempt (only in development)
        print(f"Login attempt for email: {email}")

        # Check if email or password is missing
        if not email or not password:
            return Response({
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # First check if a user with this email exists
        try:
            user = User.objects.get(email=email)
            print(f"User found: {user.email}, is_superuser: {user.is_superuser}")

            # Check if user has admin role
            has_admin_role = False
            if hasattr(user, 'role'):
                has_admin_role = user.role == 'admin'
                print(f"User role check: {user.role}, has admin role: {has_admin_role}")

            # Check if user is superuser or has admin role
            is_admin = user.is_superuser or has_admin_role

            # Verify password
            password_valid = user.check_password(password)
            print(f"Password check: {password_valid}")

            if is_admin and password_valid:
                # Create or get token
                token, created = Token.objects.get_or_create(user=user)

                return Response({
                    'token': token.key,
                    'message': 'Login successful',
                    'user_id': user.id,
                    'email': user.email,
                    'is_admin': True
                }, status=status.HTTP_200_OK)
            elif not is_admin:
                return Response({
                    'error': 'This user does not have admin privileges'
                }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'error': 'Invalid password'
                }, status=status.HTTP_401_UNAUTHORIZED)

        except User.DoesNotExist:
            print(f"User not found with email: {email}")
            # User doesn't exist, check against hardcoded admin credentials
            pass

        # Check against hardcoded credentials as fallback
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            print("Using hardcoded admin credentials")
            # Either get existing admin user or create one if it doesn't exist
            try:
                admin_user = User.objects.get(email=ADMIN_EMAIL)
                print(f"Found hardcoded admin user: {admin_user.email}")
            except User.DoesNotExist:
                print("Creating new hardcoded admin user")
                # If using default User model
                if hasattr(User, 'username'):
                    admin_user = User.objects.create(
                        username='admin',  # Username is required in default User model
                        email=ADMIN_EMAIL,
                        is_staff=True,
                        is_superuser=True,
                    )
                    if hasattr(admin_user, 'role'):
                        admin_user.role = 'admin'
                    admin_user.set_password(ADMIN_PASSWORD)
                    admin_user.save()
                else:
                    # If using custom User model where email is the username field
                    admin_user = User.objects.create(
                        email=ADMIN_EMAIL,
                        is_staff=True,
                        is_superuser=True,
                    )
                    if hasattr(admin_user, 'role'):
                        admin_user.role = 'admin'
                    admin_user.set_password(ADMIN_PASSWORD)
                    admin_user.save()

            # Create or get token
            token, created = Token.objects.get_or_create(user=admin_user)

            return Response({
                'token': token.key,
                'message': 'Login successful',
                'user_id': admin_user.id,
                'email': admin_user.email,
                'is_admin': True
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)


class HomeView(APIView):
    permission_classes = [IsAdminUser]  # Only admins can access this view

    def get(self, request, *args, **kwargs):
        return Response({
            'message': 'Welcome to Admin Dashboard'
        }, status=status.HTTP_200_OK)


# -------------------------Template views-------------------------------------
# @login_required(login_url='admin-signup/')
# @ensure_csrf_cookie  # This adds CSRF token to the response
def admin_login_page(request):
    return render(request, 'admin_login.html')


def is_admin(user):
    return user.is_staff

# @login_required(login_url='users_managment/')
# @user_passes_test(is_admin)
def admin_dashboard_page(request):
    return render(request, 'home.html')


# ------------------------------------Admin signup view for API-----------------------------------
class AdminSignupView(APIView):
    permission_classes = [IsAdminUser]  # Only existing admins can create new admins

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        username = request.data.get('username')

        if not email or not password:
            return Response({
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'User with this email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new admin user
        try:
            # Handle both username-based and email-based User models
            if hasattr(User, 'username') and User._meta.get_field('username').unique:
                if not username:
                    # Generate username from email if not provided
                    username = email.split('@')[0]
                    # Make sure username is unique
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1

                admin_user = User.objects.create(
                    username=username,
                    email=email,
                    is_staff=True,
                    is_superuser=True
                )
            else:
                # Email-based User model
                admin_user = User.objects.create(
                    email=email,
                    is_staff=True,
                    is_superuser=True
                )

            # Set role if available
            if hasattr(admin_user, 'role'):
                admin_user.role = 'admin'

            admin_user.set_password(password)
            admin_user.save()

            # Create token for the new admin
            token, created = Token.objects.get_or_create(user=admin_user)

            return Response({
                'message': 'Admin user created successfully',
                'email': email,
                'token': token.key
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def admin_signup_page(request):
    return render(request, 'admin_signup.html', )
# ---------------------------------------User CRUD Orignial ADMIN------------------------------------


from rest_framework import generics, status
from rest_framework.permissions import AllowAny  # Changed from IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer

User = get_user_model()


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  # Allow anyone to create users

    def perform_create(self, serializer):
        user = serializer.save()
        Token.objects.get_or_create(user=user)  # Still create a token for the new user

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        token, _ = Token.objects.get_or_create(user=serializer.instance)

        response_data = {
            'message': 'User created successfully',
            'user_id': serializer.instance.id,
            'email': serializer.instance.email,
            'username': serializer.instance.username,
            'role': serializer.instance.role,
            'token': token.key
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

def user_management_ui(request):
    # Render the HTML template
    return render(request, 'users_managment.html')


# Add the template view for the user creation page

def user_create_page(request):
    return render(request, 'user_create.html')




# -------------------------------USER SIDE API----------------------------------------




# ------------------------------- User Login ----------------------------------------

class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get("phone_number")
        password = request.data.get("password")

        if not phone_number or not password:
            return Response({"error": "Phone number and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, phone_number=phone_number, password=password)

        if user:
            token, _ = Token.objects.get_or_create(user=user)

            user_data = {
                "token": token.key,
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": "admin" if user.is_staff else "user",
                "is_active": user.is_active,
                "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
                "phone_number": user.phone_number,
                "address": user.address if hasattr(user, "address") else "",
            }

            return Response(user_data, status=status.HTTP_200_OK)

        return Response({"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------- User Profile (Fetch Current User Data) -------------------------------------

class UserProfileView(APIView):
    permission_classes = [AllowAny]  # Only logged-in users can access

    def get(self, request):
        user = request.user

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": "admin" if user.is_staff else "user",
            "is_active": user.is_active,
            "date_joined": user.date_joined,
            "phone_number": getattr(user, "phone_number", ""),
            "address": getattr(user, "address", "")
        }

        return Response(user_data, status=status.HTTP_200_OK)

# ---------------------------- User Logout -------------------------------------

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Only logged-in users can log out

    def post(self, request):
        try:
            token = Token.objects.get(user=request.user)
            token.delete()  # Remove the token from the database
            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({"error": "Invalid request or already logged out"}, status=status.HTTP_400_BAD_REQUEST)









