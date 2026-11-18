from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, UserUpdateForm, ProfileUpdateForm
from .models import UserProfile

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create user profile with selected role
            role = form.cleaned_data.get('role', 'customer')
            UserProfile.objects.create(user=user, role=role)
            
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def dashboard_router(request):
    """Routes user to their specific role dashboard and prevents cross-role access."""
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'admin':
        return redirect('admin_dashboard')
    return redirect('customer_dashboard')

@login_required
def admin_dashboard(request):
    if request.user.profile.role != 'admin':
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
    return render(request, 'accounts/admin_dashboard.html')

@login_required
def customer_dashboard(request):
    if request.user.profile.role != 'customer':
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
    return render(request, 'accounts/customer_dashboard.html')

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })