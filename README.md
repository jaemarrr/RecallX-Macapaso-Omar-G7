# RecallX

Active-recall study app (Django + PostgreSQL/Supabase).

## Core feature: Decks, Flashcards and Study Sessions
Students create decks, add flashcards, and run study sessions. Each session quizzes the cards that are due
(question first, reveal answer, mark "I got it" / "I missed it"). Answers move cards between Leitner boxes
(1-5) and set the next review date. Admins see system stats and can view or delete any deck.

Standard features: registration, login/logout, role-based dashboards (Student / Admin), user profile.

## Setup
1. `python -m venv venv` and activate it
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `SECRET_KEY` and `DATABASE_URL` (Supabase connection string)
4. `python manage.py migrate`
5. `python manage.py createsuperuser` (this account gets the Admin role)
6. `python manage.py runserver`

Registration creates Student accounts only.
