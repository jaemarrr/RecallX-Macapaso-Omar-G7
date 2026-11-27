from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Deck, Flashcard, StudySession


class DeckFlowTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user('a', 'a@x.com', 'pass12345!')
        self.b = User.objects.create_user('b', 'b@x.com', 'pass12345!')
        self.admin = User.objects.create_superuser('adm', 'adm@x.com', 'pass12345!')
        self.client.login(username='a', password='pass12345!')

    def make_deck(self, owner=None, title='Networking'):
        return Deck.objects.create(owner=owner or self.a, title=title)

    def test_deck_crud_and_validation(self):
        r = self.client.post(reverse('deck_create'), {'title': 'ab'})
        self.assertContains(r, 'at least 3 characters')
        self.client.post(reverse('deck_create'), {'title': 'Databases', 'subject': 'IT'})
        deck = Deck.objects.get(title='Databases')
        self.assertEqual(deck.owner, self.a)
        dup = self.client.post(reverse('deck_create'), {'title': 'databases'})
        self.assertContains(dup, 'already have a deck')
        self.client.post(reverse('deck_update', args=[deck.pk]), {'title': 'DB Systems'})
        deck.refresh_from_db()
        self.assertEqual(deck.title, 'DB Systems')
        self.client.post(reverse('deck_delete', args=[deck.pk]))
        self.assertFalse(Deck.objects.filter(pk=deck.pk).exists())

    def test_card_crud_and_duplicate_rule(self):
        deck = self.make_deck()
        url = reverse('card_create', args=[deck.pk])
        self.client.post(url, {'question': 'What is TCP?', 'answer': 'A protocol'})
        self.assertEqual(deck.cards.count(), 1)
        dup = self.client.post(url, {'question': 'what is tcp?', 'answer': 'x'})
        self.assertContains(dup, 'already exists')
        self.assertContains(self.client.post(url, {'question': 'What is UDP?', 'answer': '  '}), 'required')
        card = deck.cards.first()
        self.client.post(reverse('card_update', args=[card.pk]), {'question': 'What is TCP exactly?', 'answer': 'Reliable'})
        card.refresh_from_db()
        self.assertEqual(card.answer, 'Reliable')
        self.client.post(reverse('card_delete', args=[card.pk]))
        self.assertEqual(deck.cards.count(), 0)

    def test_users_cannot_touch_others_records(self):
        deck = self.make_deck(owner=self.b, title='Private')
        card = Flashcard.objects.create(deck=deck, question='Secret?', answer='Yes')
        self.assertEqual(self.client.get(reverse('deck_detail', args=[deck.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('deck_delete', args=[deck.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('card_delete', args=[card.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('study_start', args=[deck.pk])).status_code, 404)

    def test_admin_can_view_and_delete_any_deck_but_not_edit(self):
        deck = self.make_deck()
        self.client.login(username='adm', password='pass12345!')
        self.assertEqual(self.client.get(reverse('deck_detail', args=[deck.pk])).status_code, 200)
        self.assertRedirects(self.client.get(reverse('deck_create')), reverse('dashboard'), fetch_redirect_response=False)
        self.client.post(reverse('deck_delete', args=[deck.pk]))
        self.assertFalse(Deck.objects.filter(pk=deck.pk).exists())

    def test_study_session_end_to_end(self):
        deck = self.make_deck()
        c1 = Flashcard.objects.create(deck=deck, question='Question one?', answer='A1')
        c2 = Flashcard.objects.create(deck=deck, question='Question two?', answer='A2')
        r = self.client.post(reverse('study_start', args=[deck.pk]))
        session = StudySession.objects.get()
        self.assertRedirects(r, reverse('study_session', args=[session.pk]))
        self.client.post(reverse('study_answer', args=[session.pk]), {'result': 'correct'})
        self.client.post(reverse('study_answer', args=[session.pk]), {'result': 'wrong'})
        self.assertRedirects(self.client.get(reverse('study_session', args=[session.pk])), reverse('study_summary', args=[session.pk]))
        session.refresh_from_db()
        self.assertIsNotNone(session.completed_at)
        self.assertEqual((session.correct, session.total, session.score_percent), (1, 2, 50))
        c1.refresh_from_db(); c2.refresh_from_db()
        self.assertEqual((c1.box, c1.times_correct), (2, 1))
        self.assertEqual((c2.box, c2.times_wrong), (1, 1))
        self.assertGreater(c1.next_review, c2.next_review)
        self.assertContains(self.client.get(reverse('student_dashboard')), 'Networking')

    def test_study_blocked_when_no_cards(self):
        deck = self.make_deck()
        r = self.client.post(reverse('study_start', args=[deck.pk]), follow=True)
        self.assertContains(r, 'Add at least one flashcard')
