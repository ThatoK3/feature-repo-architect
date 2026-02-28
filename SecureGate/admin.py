from django.contrib import admin
from .models import Application, Function, UserAccess, FunctionAccess, PasswordResetRequest

# Entity-Relationship Diagram (ERD):
"""
    +-----------------------+
    |      Application      |
    +-----------------------+
    | id (PK)               |
    | name                  |
    | url                   |
    | description           |
    +-----------------------+
            | 1
            |
            |
            |
            | 1
    +-----------------------+
    |       Function        |
    +-----------------------+
    | id (PK)               |
    | name                  |
    | description           |
    | application_id (FK)   |
    +-----------------------+
            | 1
            |
            |
            |
            |
            | N
    +-----------------------+
    |      UserAccess       |
    +-----------------------+
    | id (PK)               |
    | user_id (FK)          |
    | application_id (FK)   |
    +-----------------------+
            | 1
            |
            |
            |
            |
            | N
    +-----------------------+
    |     FunctionAccess    |
    +-----------------------+
    | id (PK)               |
    | user_id (FK)          |
    | function_id (FK)      |
    +-----------------------+
"""

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """
    Admin interface for managing applications.
    """
    list_display = ('name', 'url', 'description')

@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing functions.
    """
    list_display = ('name', 'description', 'application')

@admin.register(UserAccess)
class UserAccessAdmin(admin.ModelAdmin):
    """
    Admin interface for managing user access to applications and functions.
    """
    list_display = ('user', 'application', 'get_functions')

    def get_functions(self, obj):
        """
        Custom method to display functions associated with the user access.
        """
        return ", ".join([function.name for function in obj.functions.all()])

@admin.register(FunctionAccess)
class FunctionAccessAdmin(admin.ModelAdmin):
    """
    Admin interface for managing user access to functions.
    """
    list_display = ('user', 'function')



@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'request_date', 'password_change_date']
    search_fields = ['username', 'email', 'ticket__ticket_reference']
    list_filter = ['request_date', 'password_change_date']



    