from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import redirect, render

from decks.models import Deck, Flashcard, StudySession

from .decorators import role_required
from .forms import ProfileUpdateForm, RegisterForm, UserUpdateForm
from .models import Profile


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to RecallX, {user.first_name}! Your account was created.')
            return redirect('dashboard')
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    if request.user.profile.role == Profile.ADMIN:
        return redirect('admin_dashboard')
    return redirect('student_dashboard')


@role_required(Profile.STUDENT)
def student_dashboard(request):
    from django.utils import timezone
    today = timezone.localdate()
    decks = list(Deck.objects.filter(owner=request.user).annotate(total=Count('cards')))
    for d in decks:
        d.due = d.cards.filter(next_review__lte=today).count()
    sessions = StudySession.objects.filter(user=request.user).select_related('deck')[:5]
    return render(request, 'accounts/student_dashboard.html', {
        'decks': decks,
        'sessions': sessions,
        'total_due': sum(d.due for d in decks),
    })


@role_required(Profile.ADMIN)
def admin_dashboard(request):
    decks = Deck.objects.select_related('owner').annotate(total=Count('cards'))
    return render(request, 'accounts/admin_dashboard.html', {
        'user_count': User.objects.count(),
        'deck_count': Deck.objects.count(),
        'card_count': Flashcard.objects.count(),
        'session_count': StudySession.objects.count(),
        'decks': decks,
    })


@login_required
def profile(request):
    user_form = UserUpdateForm(request.POST or None, instance=request.user)
    profile_form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=request.user.profile)
    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was updated.')
            return redirect('profile')
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'accounts/profile.html', {'user_form': user_form, 'profile_form': profile_form})
