import uuid
from random import randint
from django.utils.crypto import get_random_string
from .models import Ticket

def generate_ticket_reference(ticket_type):
    """
    Generate a unique ticket reference.
    """
    while True:
        # Generate a random 8-character alphanumeric string
        reference = get_random_string(length=8)

        # Check if a ticket with this reference already exists
        if not Ticket.objects.filter(ticket_reference=reference).exists():
            # Ensure that the reference starts with 'I' for incidents or 'R' for requests
            prefix = 'I' if ticket_type == 'incident' else 'R'
            reference = prefix + reference[1:]

            return reference