# accounts/urls.py
from django.views.generic import RedirectView
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('startups/', views.startups_list, name='startups_list'),
    path('startups/<int:startup_id>/', views.startup_detail, name='startup_detail'),
    path('investments/', views.investments, name='investments'),
    path('news/', views.news, name='news'),
    path('news/<int:article_id>/', views.news_detail, name='news_detail'),
    path('news/<int:article_id>/delete/', views.delete_news, name='delete_news'),
    path('cosmochat/', views.cosmochat, name='cosmochat'),
    path('cosmochat/<int:chat_id>/', views.get_chat_messages, name='get_chat_messages'),
    path('cosmochat/send-message/', views.send_message, name='send_message'),
    path('cosmochat/mark-read/<int:chat_id>/', views.mark_messages_read, name='mark_messages_read'),
    path('cosmochat/start-chat/<int:user_id>/', views.start_chat, name='start_chat'),
    path('cosmochat/add-participant/<int:chat_id>/', views.add_participant, name='add_participant'),
    path('cosmochat/leave-chat/<int:chat_id>/', views.leave_chat, name='leave_chat'),
    path('cosmochat/create-group-chat/', views.create_group_chat, name='create_group_chat'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.profile, name='user_profile'),  # Новый маршрут
    path('create-startup/', views.create_startup, name='create_startup'),
    path('create-startup/success/', views.startup_creation_success, name='startup_creation_success'),
    path('edit-startup/<int:startup_id>/', views.edit_startup, name='edit_startup'),
    path('moderator-dashboard/', views.moderator_dashboard, name='moderator_dashboard'),
    path('approve-startup/<int:startup_id>/', views.approve_startup, name='approve_startup'),
    path('reject-startup/<int:startup_id>/', views.reject_startup, name='reject_startup'),
    path('vote-startup/<int:startup_id>/', views.vote_startup, name='vote_startup'),
    path('invest/<int:startup_id>/', views.invest, name='invest'),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('planetary-system/', views.planetary_system, name='planetary_system'),  # Новый маршрут
    path('my_startups/', views.my_startups, name='my_startups'),  # Изменяем my-startups на my_startups
    # URL для подгрузки похожих стартапов - ИСПРАВЛЯЕМ ТИП ID НА INT
    path('load_similar_startups/<int:startup_id>/', views.load_similar_startups, name='load_similar_startups'),
    path('deals/', views.deals_view, name='deals_page'), # Новый маршрут для страницы Сделки
    path('notifications/', views.notifications_view, name='notifications_page'), # Новый маршрут для страницы Уведомления
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.png', permanent=True)),
]