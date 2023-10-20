from django.shortcuts import render, redirect
from users_app.forms import RegisterForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def register(request):
    if request.method=="POST":
        register_form = RegisterForm(request.POST)    
        if register_form.is_valid():
            register_form.save()
            messages.success(request, f'Account created successfully.  Login to get started.')
            return redirect('register')
    else:
        register_form = RegisterForm()
    return render(request, 'register.html', {'register_form': register_form})