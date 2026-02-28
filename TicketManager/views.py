from django.http import JsonResponse
from django.utils import timezone
from .models import Ticket
from .utils import generate_ticket_reference  

def create_ticket(request):
    if request.method == 'POST':
        # Process form data
        requester = request.user if request.user.is_authenticated else None
        description = request.POST.get('description')
        ticket_type = request.POST.get('ticket_type')

        # Check if description is provided
        if not description:
            return JsonResponse({'error': 'Description is required'}, status=400)

        # Generate a unique ticket reference
        ticket_reference = generate_ticket_reference(ticket_type.lower())

        # Create the new ticket
        ticket = Ticket.objects.create(
            requester=requester,
            ticket_reference=ticket_reference,
            description=description,
            ticket_type=ticket_type,
            status='IN_PROGRESS',  
            open_date=timezone.now(),
        )

        # Return JSON response
        return JsonResponse({'reference': ticket_reference, 'status': 'success'})

    else:
        # Return JSON response for invalid request method
        return JsonResponse({'error': 'Invalid request method'}, status=405)