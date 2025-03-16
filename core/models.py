from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

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
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_tasks")
    shared_with = models.ManyToManyField(User, related_name="shared_tasks", blank=True)

    def __str__(self):
        return self.title
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at'], name='idx_created_at'),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.notify_users()

    def notify_users(self):
        """ Notify users when a task is updated. """
        users_to_notify = self.shared_with.all()
        channel_layer = get_channel_layer()
        
        for user in users_to_notify:
            notification = Notification.objects.create(
                user=user,
                message=f"Task '{self.title}' has been updated."
            )
            async_to_sync(channel_layer.group_send)(
                f"notifications_{user.id}",
                {
                    "type": "send_notification",
                    "message": notification.message,
                    "timestamp": str(notification.created_at)
                }
            )

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

