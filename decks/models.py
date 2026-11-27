from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

# Leitner box -> days until the card is due again after a correct answer
BOX_INTERVALS = {1: 1, 2: 2, 3: 4, 4: 7, 5: 14}
MAX_CARDS_PER_DECK = 200


class Deck(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='decks')
    title = models.CharField(max_length=100)
    subject = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [models.UniqueConstraint(fields=['owner', 'title'], name='unique_deck_title_per_owner')]

    def __str__(self):
        return self.title

    def due_cards(self):
        return self.cards.filter(next_review__lte=timezone.localdate())


class Flashcard(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='cards')
    question = models.TextField()
    answer = models.TextField()
    hint = models.CharField(max_length=200, blank=True)
    box = models.PositiveSmallIntegerField(default=1)
    next_review = models.DateField(default=timezone.localdate)
    times_correct = models.PositiveIntegerField(default=0)
    times_wrong = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.question[:50]

    def record_answer(self, correct):
        today = timezone.localdate()
        if correct:
            self.box = min(self.box + 1, 5)
            self.times_correct += 1
            self.next_review = today + timedelta(days=BOX_INTERVALS[self.box])
        else:
            self.box = 1
            self.times_wrong += 1
            self.next_review = today
        self.save()


class StudySession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_sessions')
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    @property
    def total(self):
        return self.answers.count()

    @property
    def correct(self):
        return self.answers.filter(was_correct=True).count()

    @property
    def score_percent(self):
        return round(100 * self.correct / self.total) if self.total else 0

    def next_answer(self):
        return self.answers.filter(was_correct__isnull=True).select_related('card').first()


class SessionAnswer(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='answers')
    card = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name='answers')
    was_correct = models.BooleanField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['id']
