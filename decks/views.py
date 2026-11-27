from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import Profile

from .forms import DeckForm, FlashcardForm
from .models import Deck, Flashcard, SessionAnswer, StudySession

STUDENT = Profile.STUDENT
ADMIN = Profile.ADMIN


def _own_deck(request, pk):
    # Students can only reach their own decks; anything else is a 404.
    return get_object_or_404(Deck, pk=pk, owner=request.user)


# ---------- Deck CRUD ----------

@role_required(STUDENT)
def deck_create(request):
    form = DeckForm(request.POST or None, owner=request.user)
    if request.method == 'POST':
        if form.is_valid():
            deck = form.save(commit=False)
            deck.owner = request.user
            deck.save()
            messages.success(request, f'Deck "{deck.title}" created. Add your first flashcard!')
            return redirect('deck_detail', pk=deck.pk)
        messages.error(request, 'Could not create the deck. Check the errors below.')
    return render(request, 'decks/deck_form.html', {'form': form, 'heading': 'New deck'})


@login_required
def deck_detail(request, pk):
    if request.user.profile.role == ADMIN:
        deck = get_object_or_404(Deck, pk=pk)  # admins may view any deck (read-only)
    else:
        deck = _own_deck(request, pk)
    return render(request, 'decks/deck_detail.html', {
        'deck': deck,
        'cards': deck.cards.all(),
        'due_count': deck.due_cards().count(),
        'is_owner': deck.owner_id == request.user.id,
    })


@role_required(STUDENT)
def deck_update(request, pk):
    deck = _own_deck(request, pk)
    form = DeckForm(request.POST or None, instance=deck, owner=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Deck updated.')
            return redirect('deck_detail', pk=deck.pk)
        messages.error(request, 'Could not update the deck. Check the errors below.')
    return render(request, 'decks/deck_form.html', {'form': form, 'heading': 'Edit deck'})


@login_required
def deck_delete(request, pk):
    if request.user.profile.role == ADMIN:
        deck = get_object_or_404(Deck, pk=pk)
        next_url = 'admin_dashboard'
    else:
        deck = _own_deck(request, pk)
        next_url = 'student_dashboard'
    if request.method == 'POST':
        title = deck.title
        deck.delete()
        messages.success(request, f'Deck "{title}" and its cards were deleted.')
        return redirect(next_url)
    return render(request, 'decks/confirm_delete.html', {
        'object_name': f'deck "{deck.title}" and all {deck.cards.count()} of its cards',
        'cancel_url': 'deck_detail', 'cancel_pk': deck.pk,
    })


# ---------- Flashcard CRUD ----------

@role_required(STUDENT)
def card_create(request, deck_pk):
    deck = _own_deck(request, deck_pk)
    form = FlashcardForm(request.POST or None, deck=deck)
    if request.method == 'POST':
        if form.is_valid():
            card = form.save(commit=False)
            card.deck = deck
            card.save()
            deck.save()  # bump updated_at
            messages.success(request, 'Flashcard added.')
            if 'save_another' in request.POST:
                return redirect('card_create', deck_pk=deck.pk)
            return redirect('deck_detail', pk=deck.pk)
        messages.error(request, 'Could not save the flashcard. Check the errors below.')
    return render(request, 'decks/card_form.html', {'form': form, 'deck': deck, 'heading': 'New flashcard'})


@role_required(STUDENT)
def card_update(request, pk):
    card = get_object_or_404(Flashcard, pk=pk, deck__owner=request.user)
    form = FlashcardForm(request.POST or None, instance=card, deck=card.deck)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Flashcard updated.')
            return redirect('deck_detail', pk=card.deck_id)
        messages.error(request, 'Could not update the flashcard. Check the errors below.')
    return render(request, 'decks/card_form.html', {'form': form, 'deck': card.deck, 'heading': 'Edit flashcard'})


@role_required(STUDENT)
def card_delete(request, pk):
    card = get_object_or_404(Flashcard, pk=pk, deck__owner=request.user)
    if request.method == 'POST':
        deck_id = card.deck_id
        card.delete()
        messages.success(request, 'Flashcard deleted.')
        return redirect('deck_detail', pk=deck_id)
    return render(request, 'decks/confirm_delete.html', {
        'object_name': 'this flashcard',
        'cancel_url': 'deck_detail', 'cancel_pk': card.deck_id,
    })


# ---------- Study session (active recall) ----------

@role_required(STUDENT)
@require_POST
def study_start(request, deck_pk):
    deck = _own_deck(request, deck_pk)
    due = list(deck.due_cards().order_by('box', 'next_review')[:20])
    if not deck.cards.exists():
        messages.error(request, 'Add at least one flashcard before studying.')
        return redirect('deck_detail', pk=deck.pk)
    if not due:
        messages.success(request, 'Nothing is due in this deck right now. Come back later!')
        return redirect('deck_detail', pk=deck.pk)
    session = StudySession.objects.create(user=request.user, deck=deck)
    SessionAnswer.objects.bulk_create([SessionAnswer(session=session, card=c) for c in due])
    return redirect('study_session', pk=session.pk)


@role_required(STUDENT)
def study_session(request, pk):
    session = get_object_or_404(StudySession, pk=pk, user=request.user)
    if session.completed_at:
        return redirect('study_summary', pk=session.pk)
    current = session.next_answer()
    if current is None:
        session.completed_at = timezone.now()
        session.save()
        return redirect('study_summary', pk=session.pk)
    done = session.answers.filter(was_correct__isnull=False).count()
    return render(request, 'decks/study.html', {
        'session': session, 'answer': current, 'done': done, 'total': session.total,
        'reveal': request.GET.get('reveal') == '1',
    })


@role_required(STUDENT)
@require_POST
def study_answer(request, pk):
    session = get_object_or_404(StudySession, pk=pk, user=request.user, completed_at__isnull=True)
    current = session.next_answer()
    result = request.POST.get('result')
    if current is None or result not in ('correct', 'wrong'):
        messages.error(request, 'Invalid answer submitted.')
        return redirect('study_session', pk=session.pk)
    correct = result == 'correct'
    current.was_correct = correct
    current.answered_at = timezone.now()
    current.save()
    current.card.record_answer(correct)
    return redirect('study_session', pk=session.pk)


@role_required(STUDENT)
def study_summary(request, pk):
    session = get_object_or_404(StudySession, pk=pk, user=request.user)
    return render(request, 'decks/study_summary.html', {
        'session': session,
        'answers': session.answers.select_related('card'),
    })
