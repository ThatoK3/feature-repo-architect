from django.db import models
from django.contrib.auth.models import User

class Ticket(models.Model):
    TICKET_STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]

    ticket_reference = models.CharField(max_length=8, unique=True)
    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    ticket_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=TICKET_STATUS_CHOICES, default='IN_PROGRESS')
    open_date = models.DateTimeField(auto_now_add=True)
    resolve_date = models.DateTimeField(null=True, blank=True)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    task_comments = models.TextField(blank=True)

    def __str__(self):
        return self.ticket_reference