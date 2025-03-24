from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
import json
from django.http import JsonResponse
import logging
import os
import shutil
from django.conf import settings
from .forms import RegisterForm, LoginForm, StartupForm
from .models import Users, Startups, ReviewStatuses, UserVotes, StartupTimeline, FileStorage, EntityTypes, FileTypes

# Главная страница
def home(request):
    return render(request, 'accounts/home.html')

# Регистрация пользователя
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect('home')
        else:
            return render(request, 'accounts/register.html', {'form': form})
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

# Вход пользователя
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.email}!')
                return redirect('home')
            else:
                messages.error(request, 'Неверный email или пароль.')
        return render(request, 'accounts/login.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

# Выход пользователя
def user_logout(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('home')

# Профиль пользователя
def profile(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Пожалуйста, войдите в систему, чтобы просмотреть профиль.')
        return redirect('login')

    if request.method == 'POST' and 'avatar' in request.FILES:
        avatar = request.FILES['avatar']
        fs = FileSystemStorage(location='static/accounts/images/avatars')
        filename = f'user_{request.user.user_id}_avatar{os.path.splitext(avatar.name)[1]}'
        fs.save(filename, avatar)
        request.user.profile_picture_url = f'accounts/images/avatars/{filename}'
        request.user.save()
        messages.success(request, 'Аватарка успешно загружена!')

    return render(request, 'accounts/profile.html', {'user': request.user})

# Список одобренных стартапов
def startups_list(request):
    approved_startups = Startups.objects.filter(status='approved')
    for startup in approved_startups:
        if startup.total_voters > 0:
            startup.average_rating = float(startup.sum_votes) / startup.total_voters
        else:
            startup.average_rating = 0.0
    return render(request, 'accounts/startups_list.html', {'approved_startups': approved_startups})

# Детали стартапа
def startup_detail(request, startup_id):
    startup = get_object_or_404(Startups, startup_id=startup_id)
    creatives = FileStorage.objects.filter(
        entity_type__type_name='startup',
        entity_id=startup_id,
        file_type__type_name='creative'
    )
    proofs = FileStorage.objects.filter(
        entity_type__type_name='startup',
        entity_id=startup_id,
        file_type__type_name='proof'
    )
    timeline = StartupTimeline.objects.filter(startup=startup)
    average_rating = startup.sum_votes / startup.total_voters if startup.total_voters > 0 else 0
    return render(request, 'accounts/startup_detail.html', {
        'startup': startup,
        'creatives': creatives,
        'proofs': proofs,
        'timeline': timeline,
        'average_rating': average_rating
    })

# Страница инвестиций
def investments(request):
    return render(request, 'accounts/investments.html')

# Страница новостей
def news(request):
    return render(request, 'accounts/news.html')

# Страница юридической информации
def legal(request):
    return render(request, 'accounts/legal.html')




# Настройка логгера
logger = logging.getLogger(__name__)

@login_required
def create_startup(request):
    if request.method == 'POST':
        form = StartupForm(request.POST, request.FILES)
        if form.is_valid():
            startup = form.save(commit=False)
            startup.owner = request.user
            startup.created_at = timezone.now()
            startup.updated_at = timezone.now()
            startup.status = 'pending'
            try:
                startup.status_id = ReviewStatuses.objects.get(status_name='Pending')
            except ReviewStatuses.DoesNotExist:
                raise ValueError("Статус 'Pending' не найден в базе данных.")
            startup.save()

            # Обработка креативов
            creatives = form.cleaned_data.get('creatives', [])
            if creatives:
                creative_type = FileTypes.objects.get(type_name='creative')
                entity_type = EntityTypes.objects.get(type_name='startup')
                for creative_file in creatives:
                    # Пропускаем, если creative_file — это не файл
                    if not hasattr(creative_file, 'name'):
                        continue
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=creative_type,
                        uploaded_at=timezone.now()
                    )
                    file_storage.file_url.save(creative_file.name, creative_file, save=True)

            # Обработка пруфов
            proofs = form.cleaned_data.get('proofs', [])
            if proofs:
                proof_type = FileTypes.objects.get(type_name='proof')
                entity_type = EntityTypes.objects.get(type_name='startup')
                for proof_file in proofs:
                    # Пропускаем, если proof_file — это не файл
                    if not hasattr(proof_file, 'name'):
                        continue
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=proof_type,
                        uploaded_at=timezone.now()
                    )
                    file_storage.file_url.save(proof_file.name, proof_file, save=True)

            messages.success(request, f'Стартап "{startup.title}" успешно создан и отправлен на модерацию!')
            return redirect('profile')
        else:
            messages.error(request, 'Форма содержит ошибки.')
            return render(request, 'accounts/create_startup.html', {'form': form})
    else:
        form = StartupForm()
    return render(request, 'accounts/create_startup.html', {'form': form})

@login_required
def edit_startup(request, startup_id):
    logger.debug(f"Request method: {request.method}")
    logger.debug(f"Request POST: {request.POST}")
    logger.debug(f"Request FILES: {dict(request.FILES)}")
    
    startup = get_object_or_404(Startups, startup_id=startup_id)
    if request.user != startup.owner:
        messages.error(request, 'У вас нет прав для редактирования этого стартапа.')
        return redirect('startup_detail', startup_id=startup_id)

    if request.method == 'POST':
        form = StartupForm(request.POST, request.FILES, instance=startup)
        if form.is_valid():
            startup = form.save(commit=False)
            startup.status = 'pending'
            startup.is_edited = True
            startup.updated_at = timezone.now()
            # Устанавливаем current_step только если он передан в POST
            if 'current_step' in request.POST:
                startup.current_step = int(request.POST.get('current_step'))
            startup.save()

            # Обработка креативов
            creatives = form.cleaned_data.get('creatives', [])
            if creatives:
                logger.debug(f"Creatives found in form.cleaned_data: {creatives}")
                creative_type = FileTypes.objects.get(type_name='creative')
                entity_type = EntityTypes.objects.get(type_name='startup')
                for creative_file in creatives:
                    # Пропускаем, если creative_file — это не файл
                    if not hasattr(creative_file, 'name'):
                        continue
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=creative_type,
                        uploaded_at=timezone.now()
                    )
                    file_storage.file_url.save(creative_file.name, creative_file, save=True)

            # Обработка пруфов
            proofs = form.cleaned_data.get('proofs', [])
            if proofs:
                logger.debug(f"Proofs found in form.cleaned_data: {proofs}")
                proof_type = FileTypes.objects.get(type_name='proof')
                entity_type = EntityTypes.objects.get(type_name='startup')
                for proof_file in proofs:
                    # Пропускаем, если proof_file — это не файл
                    if not hasattr(proof_file, 'name'):
                        continue
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=proof_type,
                        uploaded_at=timezone.now()
                    )
                    file_storage.file_url.save(proof_file.name, proof_file, save=True)

            messages.success(request, f'Стартап "{startup.title}" обновлён и отправлен на модерацию.')
            return redirect('startup_detail', startup_id=startup_id)
        else:
            messages.error(request, 'Форма содержит ошибки. Проверьте введенные данные.')
            logger.error(f"Form errors: {form.errors}")
    else:
        form = StartupForm(instance=startup)
    return render(request, 'accounts/edit_startup.html', {'form': form, 'startup': startup})

# Исправленная панель модератора
def moderator_dashboard(request):
    if not request.user.is_authenticated or request.user.role.role_name != 'moderator':
        messages.error(request, 'У вас нет прав для этого действия.')
        return redirect('home')
    pending_startups = Startups.objects.filter(status='pending')
    return render(request, 'accounts/moderator_dashboard.html', {'pending_startups': pending_startups})

def approve_startup(request, startup_id):
    if not request.user.is_authenticated or request.user.role.role_name != 'moderator':
        messages.error(request, 'У вас нет прав для этого действия.')
        return redirect('home')
    startup = get_object_or_404(Startups, startup_id=startup_id)
    if request.method == 'POST':
        moderator_comment = request.POST.get('moderator_comment', '')
        startup.moderator_comment = moderator_comment
        startup.status = 'approved'
        try:
            startup.status_id = ReviewStatuses.objects.get(status_name='Approved')
        except ReviewStatuses.DoesNotExist:
            raise ValueError("Статус 'Approved' не найден в базе данных.")
        startup.save()
        messages.success(request, 'Стартап одобрен.')
    return redirect('moderator_dashboard')

def reject_startup(request, startup_id):
    if not request.user.is_authenticated or request.user.role.role_name != 'moderator':
        messages.error(request, 'У вас нет прав для этого действия.')
        return redirect('home')
    startup = get_object_or_404(Startups, startup_id=startup_id)
    if request.method == 'POST':
        moderator_comment = request.POST.get('moderator_comment', '')
        startup.moderator_comment = moderator_comment
        startup.status = 'rejected'
        try:
            startup.status_id = ReviewStatuses.objects.get(status_name='Rejected')
        except ReviewStatuses.DoesNotExist:
            raise ValueError("Статус 'Rejected' не найден в базе данных.")
        startup.save()
        messages.success(request, 'Стартап отклонен.')
    return redirect('moderator_dashboard')

# Голосование за стартап
@login_required
def vote_startup(request, startup_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

    startup = get_object_or_404(Startups, startup_id=startup_id)
    rating = int(request.POST.get('rating', 0))

    if not 1 <= rating <= 5:
        return JsonResponse({'success': False, 'error': 'Недопустимое значение рейтинга'})

    if UserVotes.objects.filter(user=request.user, startup=startup).exists():
        return JsonResponse({'success': False, 'error': 'Вы уже голосовали за этот стартап'})

    UserVotes.objects.create(user=request.user, startup=startup, rating=rating)
    startup.total_voters += 1
    startup.sum_votes += rating
    startup.save()

    average_rating = startup.sum_votes / startup.total_voters if startup.total_voters > 0 else 0
    return JsonResponse({'success': True, 'average_rating': average_rating})