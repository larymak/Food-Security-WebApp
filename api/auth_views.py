from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.views import View
from .forms import UserRegistrationForm

class RegisterView(View):
    def get(self, request):
        form = UserRegistrationForm()
        return render(request, 'api/register.html', {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.user_type == 'donor':
                return redirect('donor_dashboard')
            else:
                return redirect('recipient_dashboard')
        return render(request, 'api/register.html', {'form': form})

class LoginView(View):
    def get(self, request):
        return render(request, 'api/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.user_type == 'donor':
                return redirect('donor_dashboard')
            else:
                return redirect('recipient_dashboard')
        else:
            return render(request, 'api/login.html', {'error': 'Invalid credentials'})