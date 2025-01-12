from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm


def user_login(request):
    error_message = None
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home_page')
            else:
                error_message = 'Invalid username or password'
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form, 'error_message': error_message})

def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            first_error = next(iter(form.errors.items()))
            error_message = f"{first_error[0].capitalize()}: {', '.join(first_error[1])}"
            return render(request, 'authentication/register.html', {'form': form, 'error_message': error_message})
    else:
        form = UserCreationForm()
    return render(request, 'authentication/register.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')
