from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
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
    """Adds a user to the shared list."""
    if request.method == "POST":
        task = get_object_or_404(Task, id=task_id, owner=request.user)

        try:
            data = json.loads(request.body)
            username = data.get("username")
            user = User.objects.get(username=username)

            if user in task.shared_with.all():
                return JsonResponse({"message": "User already has access"}, status=400)

            task.shared_with.add(user)
            return JsonResponse({"message": f"User {username} added successfully"})

        except User.DoesNotExist:
            return JsonResponse({"message": "User does not exist"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
@login_required
def remove_shared_user(request, task_id):
    """Removes a user from the shared list and sends a notification."""
    if request.method == "POST":
        task = get_object_or_404(Task, id=task_id, owner=request.user)

        try:
            data = json.loads(request.body)
            username = data.get("username")
            user = User.objects.get(username=username)

            if user not in task.shared_with.all():
                return JsonResponse({"message": "User is not shared on this task"}, status=400)

            # Remove the user from the shared task
            task.shared_with.remove(user)

            # Notify the removed user in real-time and save to DB
            channel_layer = get_channel_layer()
            message = f"⚠️ You have been removed from the task: {task.title}"
            Notification.objects.create(user=user, message=message)

            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "send_notification",
                    "message": message,
                },
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
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User is not authenticated"}, status=401)

    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")[:10]
    notifications_data = [
        {"message": n.message, "timestamp": n.created_at.strftime("%Y-%m-%d %H:%M:%S")}
        for n in notifications
    ]

    return JsonResponse({"notifications": notifications_data})

from django.db.models import Count
from django.db.models.functions import TruncWeek

"""
To effectively visualize task trends and ensure accurate representation of your data, it's essential to follow a structured approach. Here's a step-by-step guide to help you achieve this:

1. **Data Preparation:**
   - **Ensure Accurate Data Retrieval:** Verify that you're fetching the correct data for the logged-in user. This includes tasks with accurate `created_at`, `due_date`, and `status` fields.
   - **Handle Missing or Incorrect Data:** Check for any missing or inconsistent data entries that might skew the visualizations.

2. **Data Aggregation:**
   - **Resample Data Appropriately:** Depending on the desired visualization (e.g., weekly trends, monthly summaries), aggregate your data accordingly. For instance, use weekly resampling to observe weekly task completion trends.
   - **Differentiate Between Task States:** Separate tasks based on their `status` (e.g., 'Completed', 'Pending') to provide clear insights into each category.

3. **Visualization:**
   - **Choose the Right Plot Type:** Select visualization types that best represent your data. For example, line plots for trends over time, bar plots for categorical comparisons, and pie charts for distribution breakdowns.
   - **Customize Plots for Clarity:** Enhance your plots with titles, axis labels, legends, and grid lines to improve readability and interpretation.

4. **Integration into Django:**
   - **Generate Plots in Views:** Create the visualizations within your Django views, rendering them as images.
   - **Embed Plots in Templates:** Incorporate these images into your Django templates to display the visualizations on your web pages.

5. **Testing and Validation:**
   - **Verify Data Accuracy:** Cross-check the visualizations against your raw data to ensure they accurately reflect the information.
   - **Gather User Feedback:** Collect feedback from users to identify any discrepancies or areas for improvement in the visualizations.

By systematically following these steps, you can create meaningful and accurate visualizations that provide valuable insights into task trends and statuses. 
"""

def task_overview(request):
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status="Completed").count()
    pending_tasks = Task.objects.filter(status="Pending").count()

    return JsonResponse([
        {"status": "Total", "count": total_tasks},
        {"status": "Completed", "count": completed_tasks},
        {"status": "Pending", "count": pending_tasks}
    ], safe=False)

def task_trends(request):
    trends = Task.objects.annotate(week=TruncWeek("created_at")).values("week").annotate(count=Count("id")).order_by("week")

    return JsonResponse(list(trends), safe=False)

import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def task_overview(request):
    cached_data = r.get("taskAnalytics")

    if cached_data:
        return JsonResponse(json.loads(cached_data), safe=False)

    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status="Completed").count()
    pending_tasks = Task.objects.filter(status="Pending").count()

    response = [
        {"status": "Total", "count": total_tasks},
        {"status": "Completed", "count": completed_tasks},
        {"status": "Pending", "count": pending_tasks}
    ]

    r.setex("taskAnalytics", 3600, json.dumps(response))  # Cache for 1 hour
    return JsonResponse(response, safe=False)

from django.shortcuts import render

def dashboard(request):
    return render(request, "core/dashboard.html")

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from io import BytesIO


@login_required
def task_trends_graph(request):
    # Get tasks for the logged-in user
    tasks = Task.objects.filter(owner=request.user).values("created_at", "status")

    # Convert to DataFrame
    df = pd.DataFrame(list(tasks))
    df["created_at"] = pd.to_datetime(df["created_at"])

    # Aggregate tasks by week
    df_weekly = df.resample("W", on="created_at").count()

    # Generate the line plot
    plt.figure(figsize=(10, 5))  # Width, Height in inches
    sns.lineplot(data=df_weekly, x=df_weekly.index, y="status", marker="o", color="b")
    plt.title("Weekly Task Trends")
    plt.xlabel("Week")
    plt.ylabel("Number of Tasks Created")
    plt.xticks(rotation=45)
    plt.grid(True)

    # Save to a buffer
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type="image/png")

@login_required
def weekly_task_completion_trends(request):
    # Fetch completed tasks for the logged-in user
    tasks = Task.objects.filter(owner=request.user, status='Completed').values('created_at')
    df = pd.DataFrame(list(tasks))
    df['created_at'] = pd.to_datetime(df['created_at'])
    df.set_index('created_at', inplace=True)
    df_weekly = df.resample('W').size()

    # Generate the plot
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df_weekly, marker='o', color='b')
    plt.title('Weekly Task Completion Trends')
    plt.xlabel('Week')
    plt.ylabel('Number of Tasks Completed')
    plt.xticks(rotation=45)
    plt.grid(True)

    # Save plot to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')

@login_required
def monthly_task_creation_trends(request):
    # Fetch tasks for the logged-in user
    tasks = Task.objects.filter(owner=request.user).values('created_at')
    df = pd.DataFrame(list(tasks))
    df['created_at'] = pd.to_datetime(df['created_at'])
    df.set_index('created_at', inplace=True)
    df_monthly = df.resample('M').size()

    # Generate the plot
    plt.figure(figsize=(10, 5))
    sns.barplot(x=df_monthly.index.strftime('%Y-%m'), y=df_monthly.values, palette='viridis')
    plt.title('Monthly Task Creation Trends')
    plt.xlabel('Month')
    plt.ylabel('Number of Tasks Created')
    plt.xticks(rotation=45)
    plt.grid(True)

    # Save plot to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')

@login_required
def task_status_distribution(request):
    # Fetch tasks for the logged-in user
    tasks = Task.objects.filter(owner=request.user).values('status')
    df = pd.DataFrame(list(tasks))
    status_counts = df['status'].value_counts()

    # Generate the plot
    plt.figure(figsize=(8, 8))
    plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('Set2'))
    plt.title('Task Status Distribution')
    plt.axis('equal')

    # Save plot to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')

@login_required
def overdue_tasks(request):
    today = pd.Timestamp.today().normalize()
    tasks = Task.objects.filter(owner=request.user, status__in=['Pending', 'In Progress'], due_date__lt=today).values('due_date', 'title')
    df = pd.DataFrame(list(tasks))

    # Generate the plot
    plt.figure(figsize=(10, 5))
    if not df.empty:
        sns.countplot(data=df, x='due_date', palette='Reds')
        plt.title('Overdue Tasks')
        plt.xlabel('Due Date')
        plt.ylabel('Number of Overdue Tasks')
        plt.xticks(rotation=45)
        plt.grid(True)
    else:
        plt.text(0.5, 0.5, 'No Overdue Tasks', horizontalalignment='center', verticalalignment='center', fontsize=12)
        plt.axis('off')

    # Save plot to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')
# Changes End

