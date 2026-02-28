from django.contrib import admin
from .models import Ticket

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
                    "ticket_reference",
                    "requester",
                    "status",
                    "open_date",
                    "assignee",
                    )

    search_fields = ["ticket_reference"]


 