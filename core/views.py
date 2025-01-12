from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Task
from .forms import TaskForm
from django.db.models import Q


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

    tasks = Task.objects.filter(user=request.user)

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
            task.user = request.user
            task.save()
            return redirect('home_page')
    else:
        form = TaskForm()
    return render(request, 'core/task_create.html', {'form': form})

@login_required(login_url='login')
def task_update(request, pk):
    try:
        task = Task.objects.get(pk=pk, user=request.user)
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
        task = Task.objects.get(pk=pk, user=request.user)
        if request.method == 'POST':
            task.delete()
            return redirect('home_page')
        return render(request, 'core/task_confirm_delete.html', {'task': task})
    except Task.DoesNotExist:
        return HttpResponse('Task not found', status=404)

