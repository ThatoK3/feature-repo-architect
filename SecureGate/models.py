from django.db import models
from django.contrib.auth.models import User

import secrets
from django.utils import timezone
from django.core.signing import Signer

from django.contrib.auth.models import Group

class Application(models.Model):
    """
    Model representing an application.
    """
    name = models.CharField(max_length=100, help_text="Enter the name of the application.")
    display_name = models.CharField(max_length=48, null=True)
    team = models.CharField(max_length=48, null=True)
    url = models.URLField(help_text="Enter the URL of the application.")

    access_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        related_name='applications'
    )  # ForeignKey to the Group model
    
    description = models.TextField(help_text="Enter a description for the application.")

    def __str__(self):
        """
        String for representing the Application object.
        """
        return self.name

class Function(models.Model):
    """
    Model representing a function within an application.
    """
    name = models.CharField(max_length=100, help_text="Enter the name of the function.")
    description = models.TextField(help_text="Enter a description for the function.")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, help_text="Select the application this function belongs to.")

    def __str__(self):
        """
        String for representing the Function object.
        """
        return self.name

class UserAccess(models.Model):
    """
    Model representing user access to applications and functions.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Select the user.")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, help_text="Select the application.")
    functions = models.ManyToManyField(Function, blank=True, help_text="Select the functions this user can access.")

    def __str__(self):
        """
        String for representing the UserAccess object.
        """
        return f"{self.user.username} - {self.application.name}"

class FunctionAccess(models.Model):
    """
    Model representing user access to functions.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Select the user.")
    function = models.ForeignKey(Function, on_delete=models.CASCADE, help_text="Select the function.")

    def __str__(self):
        """
        String for representing the FunctionAccess object.
        """
        return f"{self.user.username} - {self.function.name}"




def generate_salt():
    return secrets.token_urlsafe(32)

class PasswordResetRequest(models.Model):
    """
    Model to store password reset requests.
    """

    username = models.CharField(max_length=100, help_text="Username of the user.")
    email = models.EmailField(help_text="Email address of the user.")
    salt = models.CharField(max_length=50, editable=False, default=generate_salt, help_text="Salt to be used for signing tokens.")
    signed_token = models.CharField(max_length=200, null=True, blank=True, help_text="Signed token for password reset link.")  
    request_date = models.DateTimeField(default=timezone.now, help_text="Date and time of the password reset request.")
    password_change_date = models.DateTimeField(null=True, blank=True, help_text="Date and time when the password was changed after the reset request.")
    ticket = models.ForeignKey('TicketManager.Ticket', on_delete=models.CASCADE, related_name='password_reset_requests', help_text="Reference to the ticket.")
    url = models.CharField(max_length=100, help_text="Password reset link.", null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Overrides the default save behavior to sign the token with the provided salt.
        """
        if not self.pk:  # Check if object is being created for the first time
            signer = Signer(salt=self.salt)
            self.signed_token = signer.sign(self.username)
            self.url = 'http://localhost:8001/reset_password?token='+ self.signed_token
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Returns a string representation of the object.
        """
        return f"Password Reset Request for {self.username} ({self.username})"