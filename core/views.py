from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.functions import ExtractWeek
from .models import Task, Notification
from .forms import TaskForm
from django.db.models import Q
import json


def task_detail(request, pk):
    try:
        task = Task.objects.get(pk=pk)
        return render(request, 'task_detail.html', {'task': task})
    except Task.DoesNotExist:
        return HttpResponse('Task not found', status=404)

@login_required(login_url='login')
def home_page(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    # print(request.user)
    tasks = Task.objects.filter(owner=request.user)

    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='Completed').count()
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return render(request, 'core/home.html', {
        'tasks': tasks,
        'query': query,
        'status_filter': status_filter,
        'progress': progress
    })

# Task CRUD operations
@login_required(login_url='login')
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            return redirect('home_page')
    else:
        form = TaskForm()
    return render(request, 'core/task_create.html', {'form': form})

@login_required(login_url='login')
def task_update(request, pk):
    try:
        task = Task.objects.get(pk=pk, owner=request.user)
        if request.method == 'POST':
            form = TaskForm(request.POST, instance=task)
            if form.is_valid():
                form.save()
                return redirect('home_page')
        else:
            form = TaskForm(instance=task)
        return render(request, 'core/task_form.html', {'form': form})
    except Task.DoesNotExist:
        return HttpResponse('Task not found', status=404)

@login_required(login_url='login')
def task_delete(request, pk):
    try:
        task = Task.objects.get(pk=pk, owner=request.user)
        if request.method == 'POST':
            task.delete()
            return redirect('home_page')
        return render(request, 'core/task_confirm_delete.html', {'task': task})
    except Task.DoesNotExist:
        return HttpResponse('Task not found', status=404)

# Changes Start
@csrf_exempt
@login_required
def share_task(request, task_id):
    """Handles sharing a task with other users and sends notifications."""
    task = get_object_or_404(Task, id=task_id)

    if request.method == "GET":
        """Render the Share Task page."""
        return render(request, "core/share_task.html", {"task": task, "shared_users": task.shared_with.all()})

    elif request.method == "PUT":
        if task.owner != request.user:
            return JsonResponse({"error": "You are not the owner of this task"}, status=403)

        try:
            data = json.loads(request.body)
            shared_usernames = data.get("users", [])
            shared_users = User.objects.filter(username__in=shared_usernames)

            # Determine new users who are added (ignore existing shared users)
            previous_shared_users = set(task.shared_with.all())  # Before updating
            task.shared_with.set(shared_users)  # Update shared users
            task.save()
            new_users = set(shared_users) - previous_shared_users  # Only new users

            # Notify each new user in real-time and save to DB
            channel_layer = get_channel_layer()
            for user in new_users:
                message = f"🚀 You have been assigned a new task: {task.title}"
                Notification.objects.create(user=user, message=message)

                async_to_sync(channel_layer.group_send)(
                    f"user_{user.id}",
                    {
                        "type": "send_notification",
                        "message": message,
                    },
                )

            return JsonResponse({"message": "Task shared successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@login_required
def get_shared_users(request, task_id):
    """Returns the list of users a task is shared with."""
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    shared_users = [{"username": user.username} for user in task.shared_with.all()]
    return JsonResponse({"shared_users": shared_users})

@csrf_exempt
@login_required
def add_shared_user(request, task_id):
    """Adds a user to the shared list and creates a notification."""
    if request.method == "POST":
        task = get_object_or_404(Task, id=task_id, owner=request.user)

        try:
            data = json.loads(request.body)
            username = data.get("username")
            user = User.objects.get(username=username)

            if user in task.shared_with.all():
                return JsonResponse({"message": "User already has access"}, status=400)

            # ✅ Add the user to the shared task
            task.shared_with.add(user)

            # ✅ Create a notification for the added user
            Notification.objects.create(
                user=user,
                message=f"🚀 You have been added to the task: {task.title}"
            )

            return JsonResponse({"message": f"User {username} added successfully"})

        except User.DoesNotExist:
            return JsonResponse({"message": "User does not exist"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
@login_required
def remove_shared_user(request, task_id):
    """Removes a user from the shared list and creates a notification."""
    if request.method == "POST":
        task = get_object_or_404(Task, id=task_id, owner=request.user)

        try:
            data = json.loads(request.body)
            username = data.get("username")
            user = User.objects.get(username=username)

            if user not in task.shared_with.all():
                return JsonResponse({"message": "User is not shared on this task"}, status=400)

            # ✅ Remove the user from the shared task
            task.shared_with.remove(user)

            # ✅ Create a notification for the removed user
            Notification.objects.create(
                user=user,
                message=f"⚠️ You have been removed from the task: {task.title}"
            )

            return JsonResponse({"message": f"User {username} removed successfully"})

        except User.DoesNotExist:
            return JsonResponse({"message": "User does not exist"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)



@login_required
def get_shared_tasks(request):
    """Returns the list of tasks that are shared with the logged-in user."""
    user = request.user
    shared_tasks = Task.objects.filter(shared_with=user)

    tasks_data = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "due_date": task.due_date.strftime("%b. %d, %Y") if task.due_date else "No Due Date",
            "owner": task.owner.username,
            "is_owner": task.owner == user  # Boolean to check if logged-in user owns the task
        }
        for task in shared_tasks
    ]

    return JsonResponse({"shared_tasks": tasks_data}, status=200)

@csrf_exempt
def update_task_status(request, task_id):
    if request.method == "PUT":
        task = get_object_or_404(Task, id=task_id)
        data = json.loads(request.body)
        new_status = data.get("status")

        task.status = new_status
        task.save()

        # Notify task owner and save to DB
        channel_layer = get_channel_layer()
        Notification.objects.create(user=task.owner, message=f"Task '{task.title}' status updated to {new_status}")

        async_to_sync(channel_layer.group_send)(
            f"user_{task.owner.id}",
            {
                "type": "send_notification",
                "message": f"Task '{task.title}' status updated to {new_status}",
            },
        )

        return JsonResponse({"message": "Task status updated successfully"}, status=200)

@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    data = [{
        "message": notification.message,
        "timestamp": notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for notification in notifications]
    return JsonResponse({"notifications": data})

@login_required
def notifications_page(request):
    return render(request, 'core/notifications.html')



import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.shortcuts import render
from django.utils.timezone import now, localdate
from django.db.models import Count, Q
from .models import Task

@login_required
def dashboard(request):
    """Generate and display simple graphs for task insights."""
    
    # ✅ Task Completion Rate
    total_tasks = Task.objects.filter(owner=request.user).count()
    completed_tasks = Task.objects.filter(owner=request.user, status='Completed').count()
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # ✅ Overdue Tasks
    overdue_tasks_count = Task.objects.filter(
        owner=request.user,
        due_date__lt=localdate(),  # ✅ Ensures no timezone mismatch
        status__in=['Pending', 'In Progress']
    ).count()

    # ✅ Task Status Distribution (Pie Chart)
    status_counts = Task.objects.filter(owner=request.user).values('status').annotate(count=Count('id'))
    if status_counts:
        labels = [entry['status'] for entry in status_counts]
        values = [entry['count'] for entry in status_counts]
        plt.figure(figsize=(5, 5))
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.title("Task Status Distribution")
        status_pie_chart_img = _save_plot_to_base64()
    else:
        status_pie_chart_img = None

    return render(request, 'core/dashboard.html', {
        'completion_percentage': round(completion_percentage, 2),
        'overdue_tasks': overdue_tasks_count,
        'status_pie_chart_img': status_pie_chart_img
    })

def _save_plot_to_base64():
    """Helper function to save plots as Base64 images."""
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    plt.close()
    return image_base64

