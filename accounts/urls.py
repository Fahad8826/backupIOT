# urls.py
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token


from .views import HomeView, admin_login_page, admin_dashboard_page, UserListCreateView, \
    UserRetrieveUpdateDestroyView, user_management_ui, UserLoginView, UserLogoutView, AdminLoginView, AdminSignupView, \
    SuperAdminSignupView, admin_signup_page, UserProfileView

urlpatterns = [


    path('api/admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('api/admin/home/', HomeView.as_view(), name='admin-home'),
    path('adminpage/', admin_login_page, name='admin-login-page'),
    path('admin-dashboard/', admin_dashboard_page, name='admin-dashboard-page'),

    path('users/', UserListCreateView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('api-token-auth/', obtain_auth_token, name='api-token-auth'),
    path('users_managment/',user_management_ui,name='users_managment'),


    path('api/admin/signup/', AdminSignupView.as_view(), name='admin-signup'),
    path('api/admin/super-signup/', SuperAdminSignupView.as_view(), name='super-admin-signup'),
    path('admin-signup/', admin_signup_page, name='admin-signup-page'),

    # -------------user auth flutter---------------------
    path("login/", UserLoginView.as_view(), name="user-login"),
    path("logout/", UserLogoutView.as_view(), name="user-logout"),
    path('userprofileview/',UserProfileView.as_view(),name='userprofile-view'),


]