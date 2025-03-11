from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.timezone import now

class Task(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Changes
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_tasks")
    shared_with = models.ManyToManyField(User, related_name="shared_tasks", blank=True)

    def __str__(self):
        return self.title
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at'], name='idx_created_at'),
        ]
    
    def clean(self):
        """ Validate that due_date is not before created_at and is not missing. """
        if self.due_date and self.due_date < self.created_at.date():
            raise ValidationError("Due date cannot be earlier than the creation date.")
        if not self.due_date:
            raise ValidationError("Due date is required.")

    def save(self, *args, **kwargs):
        """ Ensure validation is applied before saving the task. """
        self.full_clean()
        super().save(*args, **kwargs)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # The user receiving the notification
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

