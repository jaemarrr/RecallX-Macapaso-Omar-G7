from django import forms

from .models import MAX_CARDS_PER_DECK, Deck, Flashcard


class DeckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ('title', 'subject', 'description')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 3:
            raise forms.ValidationError('Title must be at least 3 characters.')
        dupes = Deck.objects.filter(owner=self.owner, title__iexact=title).exclude(pk=self.instance.pk)
        if dupes.exists():
            raise forms.ValidationError('You already have a deck with this title.')
        return title


class FlashcardForm(forms.ModelForm):
    class Meta:
        model = Flashcard
        fields = ('question', 'answer', 'hint')
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3}),
            'answer': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, deck=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.deck = deck

    def clean_question(self):
        q = self.cleaned_data['question'].strip()
        if len(q) < 5:
            raise forms.ValidationError('Question must be at least 5 characters.')
        if self.deck.cards.filter(question__iexact=q).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This question already exists in the deck.')
        return q

    def clean_answer(self):
        a = self.cleaned_data['answer'].strip()
        if not a:
            raise forms.ValidationError('Answer cannot be blank.')
        return a

    def clean(self):
        data = super().clean()
        if not self.instance.pk and self.deck.cards.count() >= MAX_CARDS_PER_DECK:
            raise forms.ValidationError(f'A deck can hold at most {MAX_CARDS_PER_DECK} cards.')
        return data
