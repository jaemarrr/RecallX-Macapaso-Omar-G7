from django.urls import path

from . import views

urlpatterns = [
    path('new/', views.deck_create, name='deck_create'),
    path('<int:pk>/', views.deck_detail, name='deck_detail'),
    path('<int:pk>/edit/', views.deck_update, name='deck_update'),
    path('<int:pk>/delete/', views.deck_delete, name='deck_delete'),
    path('<int:deck_pk>/cards/new/', views.card_create, name='card_create'),
    path('cards/<int:pk>/edit/', views.card_update, name='card_update'),
    path('cards/<int:pk>/delete/', views.card_delete, name='card_delete'),
    path('<int:deck_pk>/study/', views.study_start, name='study_start'),
    path('study/<int:pk>/', views.study_session, name='study_session'),
    path('study/<int:pk>/answer/', views.study_answer, name='study_answer'),
    path('study/<int:pk>/summary/', views.study_summary, name='study_summary'),
]
