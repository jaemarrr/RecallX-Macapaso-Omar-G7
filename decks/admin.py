from django.contrib import admin

from .models import Deck, Flashcard, SessionAnswer, StudySession

admin.site.register(Deck)
admin.site.register(Flashcard)
admin.site.register(StudySession)
admin.site.register(SessionAnswer)
