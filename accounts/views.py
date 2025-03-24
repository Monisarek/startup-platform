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

            # Явное сохранение логотипа
            logo = form.cleaned_data.get('logo')
            if logo:
                startup.planet_logo.save(f"startups/{startup.startup_id}/logos/{logo.name}", logo, save=True)
                logger.info(f"Логотип сохранён: {startup.planet_logo.url}")

            # Логирование информации о файлах
            logger.info("=== Отправка стартапа на модерацию ===")
            logger.info(f"Стартап ID: {startup.startup_id}")
            
            # Логотип
            if logo:
                logger.info(f"Логотип: {logo.name}, размер: {logo.size} байт")
                logger.info(f"Путь сохранения логотипа: {startup.planet_logo.url}")
            else:
                logger.info("Логотип не загружен")

            # Креативы
            creatives = form.cleaned_data.get('creatives', [])
            if creatives:
                logger.info(f"Креативы: {len(creatives)} файлов")
                for i, creative_file in enumerate(creatives, 1):
                    if hasattr(creative_file, 'name'):
                        logger.info(f"Креатив {i}: {creative_file.name}, размер: {creative_file.size} байт")
                    else:
                        logger.info(f"Креатив {i}: Неверный формат (не файл): {creative_file}")
            else:
                logger.info("Креативы не загружены")

            # Пруфы
            proofs = form.cleaned_data.get('proofs', [])
            if proofs:
                logger.info(f"Пруфы: {len(proofs)} файлов")
                for i, proof_file in enumerate(proofs, 1):
                    if hasattr(proof_file, 'name'):
                        logger.info(f"Пруф {i}: {proof_file.name}, размер: {proof_file.size} байт")
                    else:
                        logger.info(f"Пруф {i}: Неверный формат (не файл): {proof_file}")
            else:
                logger.info("Пруфы не загружены")

            # Логирование переменных окружения
            logger.info("=== Переменные окружения ===")
            for key, value in os.environ.items():
                logger.info(f"{key}: {value}")

            # Логирование настроек Yandex Object Storage
            logger.info("=== Настройки Yandex Object Storage ===")
            logger.info(f"AWS_ACCESS_KEY_ID: {getattr(settings, 'AWS_ACCESS_KEY_ID', 'Не задано')}")
            logger.info(f"AWS_SECRET_ACCESS_KEY: {getattr(settings, 'AWS_SECRET_ACCESS_KEY', 'Не задано')}")
            logger.info(f"AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Не задано')}")
            logger.info(f"AWS_S3_ENDPOINT_URL: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'Не задано')}")
            logger.info(f"AWS_DEFAULT_ACL: {getattr(settings, 'AWS_DEFAULT_ACL', 'Не задано')}")

            # Проверка подключения к Yandex Object Storage
            logger.info("=== Проверка подключения к Yandex Object Storage ===")
            try:
                from storages.backends.s3boto3 import S3Boto3Storage
                storage = S3Boto3Storage()
                test_file_name = f"test/test_file_{startup.startup_id}.txt"
                test_content = "This is a test file to check Yandex Object Storage connection."
                storage.save(test_file_name, test_content.encode('utf-8'))
                logger.info(f"Тестовый файл успешно сохранён: {test_file_name}")
                test_file_url = storage.url(test_file_name)
                logger.info(f"URL тестового файла: {test_file_url}")
                storage.delete(test_file_name)
                logger.info(f"Тестовый файл удалён: {test_file_name}")
            except Exception as e:
                logger.error(f"Ошибка подключения к Yandex Object Storage: {str(e)}")

            # Обработка креативов
            if creatives:
                creative_type = FileTypes.objects.get(type_name='creative')
                entity_type = EntityTypes.objects.get(type_name='startup')
                for creative_file in creatives:
                    if not hasattr(creative_file, 'name'):
                        logger.warning(f"Пропущен креатив, так как это не файл: {creative_file}")
                        continue
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=creative_type,
                        uploaded_at=timezone.now()
                    )
                    file_path = f"startups/{startup.startup_id}/creatives/{creative_file.name}"
                    logger.info(f"Сохранение креатива: {creative_file.name} в {file_path}")
                    file_storage.file_url.save(file_path, creative_file, save=True)
                    logger.info(f"Креатив сохранён: {file_storage.file_url.url}")

            # Обработка пруфов
            if proofs:
                proof_type = FileTypes.objects.get(type_name='proof')
                entity_type = EntityTypes.objects.get(type_name='startup')
                for proof_file in proofs:
                    if not hasattr(proof_file, 'name'):
                        logger.warning(f"Пропущен пруф, так как это не файл: {proof_file}")
                        continue
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=proof_type,
                        uploaded_at=timezone.now()
                    )
                    file_path = f"startups/{startup.startup_id}/proofs/{proof_file.name}"
                    logger.info(f"Сохранение пруфа: {proof_file.name} в {file_path}")
                    file_storage.file_url.save(file_path, proof_file, save=True)
                    logger.info(f"Пруф сохранён: {file_storage.file_url.url}")

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
            if 'current_step' in request.POST:
                startup.current_step = int(request.POST.get('current_step'))
            startup.save()

            # Явное сохранение логотипа
            logo = form.cleaned_data.get('logo')
            if logo:
                startup.planet_logo.save(f"startups/{startup.startup_id}/logos/{logo.name}", logo, save=True)
                logger.info(f"Логотип сохранён: {startup.planet_logo.url}")

            # Логирование информации о файлах
            logger.info("=== Обновление стартапа ===")
            logger.info(f"Стартап ID: {startup.startup_id}")
            
            # Логотип
            if logo:
                logger.info(f"Логотип: {logo.name}, размер: {logo.size} байт")
                logger.info(f"Путь сохранения логотипа: {startup.planet_logo.url}")
            else:
                logger.info("Логотип не загружен")

            # Креативы
            creatives = form.cleaned_data.get('creatives', [])
            if creatives:
                logger.info(f"Креативы: {len(creatives)} файлов")
                for i, creative_file in enumerate(creatives, 1):
                    if hasattr(creative_file, 'name'):
                        logger.info(f"Креатив {i}: {creative_file.name}, размер: {creative_file.size} байт")
                    else:
                        logger.info(f"Креатив {i}: Неверный формат (не файл): {creative_file}")
            else:
                logger.info("Креативы не загружены")

            # Пруфы
            proofs = form.cleaned_data.get('proofs', [])
            if proofs:
                logger.info(f"Пруфы: {len(proofs)} файлов")
                for i, proof_file in enumerate(proofs, 1):
                    if hasattr(proof_file, 'name'):
                        logger.info(f"Пруф {i}: {proof_file.name}, размер: {proof_file.size} байт")
                    else:
                        logger.info(f"Пруф {i}: Неверный формат (не файл): {proof_file}")
            else:
                logger.info("Пруфы не загружены")

            # Логирование переменных окружения
            logger.info("=== Переменные окружения ===")
            for key, value in os.environ.items():
                logger.info(f"{key}: {value}")

            # Логирование настроек Yandex Object Storage
            logger.info("=== Настройки Yandex Object Storage ===")
            logger.info(f"AWS_ACCESS_KEY_ID: {getattr(settings, 'AWS_ACCESS_KEY_ID', 'Не задано')}")
            logger.info(f"AWS_SECRET_ACCESS_KEY: {getattr(settings, 'AWS_SECRET_ACCESS_KEY', 'Не задано')}")
            logger.info(f"AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Не задано')}")
            logger.info(f"AWS_S3_ENDPOINT_URL: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'Не задано')}")
            logger.info(f"AWS_DEFAULT_ACL: {getattr(settings, 'AWS_DEFAULT_ACL', 'Не задано')}")

            # Проверка подключения к Yandex Object Storage
            logger.info("=== Проверка подключения к Yandex Object Storage ===")
            try:
                from storages.backends.s3boto3 import S3Boto3Storage
                storage = S3Boto3Storage()
                test_file_name = f"test/test_file_{startup.startup_id}.txt"
                test_content = "This is a test file to check Yandex Object Storage connection."
                storage.save(test_file_name, test_content.encode('utf-8'))
                logger.info(f"Тестовый файл успешно сохранён: {test_file_name}")
                test_file_url = storage.url(test_file_name)
                logger.info(f"URL тестового файла: {test_file_url}")
                storage.delete(test_file_name)
                logger.info(f"Тестовый файл удалён: {test_file_name}")
            except Exception as e:
                logger.error(f"Ошибка подключения к Yandex Object Storage: {str(e)}")

            # Обработка креативов
            if creatives:
                creative_type = FileTypes.objects.get(type_name='creative')
                entity_type = EntityTypes.objects.get(type_name='startup')
                for creative_file in creatives:
                    if not hasattr(creative_file, 'name'):
                        logger.warning(f"Пропущен креатив, так как это не файл: {creative_file}")
                        continue
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=creative_type,
                        uploaded_at=timezone.now()
                    )
                    file_path = f"startups/{startup.startup_id}/creatives/{creative_file.name}"
                    logger.info(f"Сохранение креатива: {creative_file.name} в {file_path}")
                    file_storage.file_url.save(file_path, creative_file, save=True)
                    logger.info(f"Креатив сохранён: {file_storage.file_url.url}")

            # Обработка пруфов
            if proofs:
                proof_type = FileTypes.objects.get(type_name='proof')
                entity_type = EntityTypes.objects.get(type_name='startup')
                for proof_file in proofs:
                    if not hasattr(proof_file, 'name'):
                        logger.warning(f"Пропущен пруф, так как это не файл: {proof_file}")
                        continue
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=proof_type,
                        uploaded_at=timezone.now()
                    )
                    file_path = f"startups/{startup.startup_id}/proofs/{proof_file.name}"
                    logger.info(f"Сохранение пруфа: {proof_file.name} в {file_path}")
                    file_storage.file_url.save(file_path, proof_file, save=True)
                    logger.info(f"Пруф сохранён: {file_storage.file_url.url}")

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