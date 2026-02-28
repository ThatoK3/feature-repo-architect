from django.contrib.auth import login, logout
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializers, ApplicationSerializer
from django.contrib.auth.models import update_last_login
from django.shortcuts import render

from django.contrib.auth.decorators import login_required 
 
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Application

from axes.decorators import axes_dispatch

from django.contrib import admin

from django_ratelimit.decorators import ratelimit

from django.contrib.auth.models import User
from django.utils import timezone
from django.core.signing import Signer, BadSignature

from TicketManager.utils import generate_ticket_reference
from TicketManager.models import Ticket

from .models import PasswordResetRequest


@ratelimit(key='user_or_ip', rate='10/5m')
def blocked_access(request):
    return render(request , 'SecureGate/lockout.html', {'page_title': "Access Denied"})


@axes_dispatch
def login_auth(request):
    return render(request , 'SecureGate/login.html', {'page_title': "Auth"})


class LoginAPIView(APIView):
    # Add CSRF protection to the view
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializers(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Log the user in, creating a session
        login(request, user)

        # Update the last login time
        update_last_login(None, user)

        return Response({"status": status.HTTP_200_OK, "message": "Login successful"})


@permission_classes([IsAuthenticated])
class LogoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Log the user out, destroying the session
        logout(request)
        return JsonResponse({"status": status.HTTP_200_OK, "message": "Logout successful"})



def choose_app(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/auth')  
    
    username = request.user.username
    if username:
        username = username.upper()
        
    return render(request, 'SecureGate/chooseapp.html', {'page_title': "ChooseApp", 'username': username})


@login_required
def unavailable_app(request):
    return render(request , 'SecureGate/appunavailable.html', {'page_title': "AppNotAvailable"})

@login_required
def noaccess_to_app(request):
    return render(request , 'SecureGate/noaccess.html', {'page_title': "NoAccess"})


@login_required
def application_list(request):
    # Get the user's groups
    user_groups = request.user.groups.all()
    
    # Retrieve all applications
    applications = Application.objects.all()
    
    # Serialize the applications
    serializer = ApplicationSerializer(applications, many=True)
    
    # Deserialize the data
    data = serializer.data
    
    # Check access for each application and set has_access
    for app in data:
        app_obj = Application.objects.get(pk=app['id'])
        has_access = app_obj.access_group in user_groups
        app['has_access'] = has_access
    
    # Return the updated data as JSON response
    return JsonResponse(data, safe=False)

# handled in TicketManager app
@ratelimit(key='user_or_ip', rate='10/5m')
def log_ticket(request):
    username = request.user.username
    welcome_nav_text = ""
    logat_nav_li = '<li class="link"><a style="text-decoration:none" href="../auth">Login</a></li>'
    goto_link = "Go to login"
    if username:
        username = username.title()
        welcome_nav_text = f"Welcome, {username}!"
        logat_nav_li = '<li class="link" onclick="submitLogout()"><a>Logout</a></li>'
        goto_link = "Go to applications"

    return render(request , 'SecureGate/logaticket.html', 
                    {'page_title': "Log a ticket", 
                    'username': username,
                    'welcome_nav_text':welcome_nav_text,
                    'logat_nav_li':logat_nav_li,
                    'goto_link':goto_link,}
                    )






# Step 1: View for requesting password reset
@ratelimit(key='user_or_ip', rate='2/5m')
def request_password_reset(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')

        # Check if the user exists with the given username and email
        try:
            user = User.objects.get(username=username, email=email)
        except User.DoesNotExist:
            # Handle invalid username or email
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, 'error': 'Invalid username or email'})

        

        # Log ticket
        ticket_reference = generate_ticket_reference('request')
        ticket = Ticket.objects.create(
            ticket_reference=ticket_reference,  
            requester=user,
            description='Password reset request',
            ticket_type='request',
            status='IN_PROGRESS',  
            open_date=timezone.now(),
        )

        

        # Generate a unique token containing user ID
        password_reset_request = PasswordResetRequest.objects.create(
            username=username,
            email=email,
            request_date=timezone.now(),
            ticket=ticket  # Associate the ticket with the password reset request
        )

        return JsonResponse({"status": status.HTTP_200_OK, 
            'message': f'Your password reset request ticket was logged under reference: {password_reset_request.ticket}'})
    else:
        return JsonResponse({"status": status.HTTP_405_METHOD_NOT_ALLOWED, 'error': 'Method not allowed'})



# Step 2: View for handling password reset post
@ratelimit(key='user_or_ip', rate='10/5m')
def reset_password(request):
    token = request.GET.get('token', None)
    
    if request.method == 'GET':
        # Check if the token is provided
        if not token:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "Token is missing."})

        # Get the salt used for signing the token
        password_reset_request = PasswordResetRequest.objects.filter(signed_token=token).first()
        if not password_reset_request:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "Invalid token."})
        
        salt = password_reset_request.salt

        # Verify the token
        try:
            signer = Signer(salt=salt)
            username = signer.unsign(token)
        except BadSignature:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "Invalid token."})

        

        # Check if the user with the provided username exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "User with this username does not exist."})

        # If token is valid and user exists, provide a form to reset the password
        return render(request , 'SecureGate/passwordreset.html', {'page_title': "Password reset"})


    elif request.method == 'POST':
        token = request.POST.get('token')
        provided_username = request.POST.get('username')
        new_password = request.POST.get('password')
        confirmed_password = request.POST.get('confirm_password')
        
        if not new_password:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "New password is missing."})

        if not confirmed_password:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "Confirmation password is missing."})

        # also handled in the front end
        if new_password!=confirmed_password:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "Passwords do not match."})

        # Check if the token is provided
        if not token:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "Token is missing."})

        # Get the salt used for signing the token
        password_reset_request = PasswordResetRequest.objects.filter(signed_token=token).first()
        if not password_reset_request:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "Invalid token."})
        
        salt = password_reset_request.salt

        # Verify the token
        try:
            signer = Signer(salt=salt)
            username = signer.unsign(token)

            # checks if username!=provided_username / token not signed by the provided user
            # username --> from token ; provided_username--> from request & SHOULD only be used here
            if username!=provided_username:
                return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "Username provided is incorrect."})

        except BadSignature:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "Invalid token."})

        # Check if the user with the provided username exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({"status": status.HTTP_400_BAD_REQUEST, "error": "User with this username does not exist."})

        # Set new password for the user and save
        user.set_password(new_password)
        user.save()

        # Set token and salt to empty strings; update change date
        password_reset_request.signed_token = ''
        password_reset_request.salt = ''
        password_reset_request.password_change_date = timezone.now()
        password_reset_request.url = '__already_used__'
        password_reset_request.save()

        ticket_reference = password_reset_request.ticket

        if ticket_reference:
            linked_ticket = Ticket.objects.filter(ticket_reference=ticket_reference).first()
            if linked_ticket:
                linked_ticket.status = 'RESOLVED'
                linked_ticket.resolve_date = timezone.now()
                linked_ticket.task_comments = f'Password changed by {user.username} (USERNAME) in the password reset view.'
                linked_ticket.save()  # Corrected typo here
            else:
                print("No linked ticket found for reference:", ticket_reference)
        else:
            print("No ticket reference found in password reset request")

        # Return success 
        return JsonResponse({"status": status.HTTP_200_OK, 'message': 'Password reset successfully'})

    else:
        return JsonResponse({"status": status.HTTP_405_METHOD_NOT_ALLOWED, 'error': 'Method not allowed'})






