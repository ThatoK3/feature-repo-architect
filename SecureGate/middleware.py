from django.shortcuts import redirect
from django.urls import reverse

class AuthenticationRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is not authenticated
        if not request.user.is_authenticated:
            # Check if the current URL is not the /auth site
            if request.path not in ['/auth', '/xloginapi/', '/auth_password_reset','/blocked-access',
                                        '/create_ticket/','/password_reset_request/', '/reset_password']:
                # If not authenticated and not on /auth, redirect to the login page
                return redirect(reverse('auth-page'))

        response = self.get_response(request)
        return response