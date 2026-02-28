from django.urls import path, include
from .views import LoginAPIView, LogoutAPIView, login_auth, choose_app, unavailable_app, noaccess_to_app, application_list, log_ticket, blocked_access, request_password_reset, reset_password

urlpatterns = [
    path('xloginapi/', LoginAPIView.as_view()),
    path('xlogoutapi/', LogoutAPIView.as_view()),
    path("auth", login_auth, name="auth-page"),
    path("auth", login_auth, name="login_auth"),
    path("", choose_app, name="choose-app-page"),
    path("unavailableapp", unavailable_app, name="unavailable-app-page"),
    path("noaccessapp", noaccess_to_app, name="no-access-to-app-page"),
    path('applications', application_list, name='application-list'),
    path('logaticket', log_ticket, name='log-a-ticket'),
    path('blocked-access', blocked_access, name='access denied'),
    path('password_reset_request/', request_password_reset, name='password reset request'),
    path('reset_password', reset_password, name='password resetter'),
]

#http://localhost:8001/reset_password?token=admin:HyFF3ySlHjD9aBxxgtLsRCOurDJKQW29-h_2LZjrDfU