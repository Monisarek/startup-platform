# accounts/views.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
import json
import logging
import os
from django.conf import settings
from .forms import RegisterForm, LoginForm, StartupForm
from .models import Users, Startups, ReviewStatuses, UserVotes, StartupTimeline, FileStorage, EntityTypes, FileTypes
from .models import creative_upload_path, proof_upload_path, video_upload_path
import uuid  # Добавляем импорт uuid

logger = logging.getLogger(__name__)

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

def startups_list(request):
    # Получаем одобренные стартапы
    approved_startups_list = Startups.objects.filter(status='approved').order_by('-created_at')
    
    # Логируем данные
    logger.info(f"Найдено одобренных стартапов: {approved_startups_list.count()}")
    for startup in approved_startups_list:
        logger.debug(f"Стартап: ID={startup.startup_id}, Title={startup.title}, Type={type(startup.startup_id)}")
    
    # Проверяем, что queryset не пустой
    if not approved_startups_list.exists():
        logger.warning("Нет стартапов со статусом 'approved'")
    
    return render(request, 'accounts/startups_list.html', {'approved_startups': approved_startups_list})

# accounts/views.py (фрагмент)

def startup_detail(request, startup_id):
    startup = get_object_or_404(Startups, startup_id=startup_id)
    timeline = StartupTimeline.objects.filter(startup=startup)
    average_rating = startup.sum_votes / startup.total_voters if startup.total_voters > 0 else 0
    return render(request, 'accounts/startup_detail.html', {
        'startup': startup,
        'logo_urls': startup.logo_urls or [],
        'creatives_urls': startup.creatives_urls or [],
        'proofs_urls': startup.proofs_urls or [],
        'video_urls': startup.video_urls or [],
        'timeline': timeline,
        'average_rating': average_rating,
        'direction_name': startup.direction.direction_name if startup.direction else 'Не указано',
        'stage_name': startup.stage.stage_name if startup.stage else 'Не указано',
        'owner_email': startup.owner.email if startup.owner else 'Не указано',
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

# Профиль пользователя
def profile(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Пожалуйста, войдите в систему, чтобы просмотреть профиль.')
        return redirect('login')

    if request.method == 'POST' and 'avatar' in request.FILES:
        avatar = request.FILES['avatar']
        filename = f'avatars/user_{request.user.user_id}_avatar{os.path.splitext(avatar.name)[1]}'
        file_path = default_storage.save(filename, avatar)
        request.user.profile_picture_url = default_storage.url(file_path)
        request.user.save()
        messages.success(request, 'Аватарка успешно загружена!')

    return render(request, 'accounts/profile.html', {'user': request.user})

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
            # Устанавливаем текущий шаг из формы
            startup.step_number = int(request.POST.get('step_number', 1))
            startup.save()

            # Сохранение всех 5 этапов таймлайна
            for i in range(1, 6):
                description = request.POST.get(f'step_description_{i}', '').strip()
                if description:  # Сохраняем только этапы с описанием
                    StartupTimeline.objects.create(
                        startup=startup,
                        step_number=i,
                        title=f"Этап {i}",
                        description=description
                    )

            # Инициализация списков для ID файлов
            logo_ids = []
            creatives_ids = []
            proofs_ids = []
            video_ids = []

            # Сохранение логотипа
            logo = form.cleaned_data.get('logo')
            if logo:
                logo_id = str(uuid.uuid4())
                file_path = f"startups/{startup.startup_id}/logos/{logo_id}_{logo.name}"
                default_storage.save(file_path, logo)
                logo_ids.append(logo_id)
                logger.info(f"Логотип сохранён с ID: {logo_id}")

            # Сохранение креативов
            creatives = form.cleaned_data.get('creatives', [])
            if creatives:
                creative_type = FileTypes.objects.get(type_name='creative')
                entity_type = EntityTypes.objects.get(type_name='startup')
                for creative_file in creatives:
                    if not hasattr(creative_file, 'name'):
                        logger.warning(f"Пропущен креатив, так как это не файл: {creative_file}")
                        continue
                    creative_id = str(uuid.uuid4())
                    file_path = f"startups/{startup.startup_id}/creatives/{creative_id}_{creative_file.name}"
                    default_storage.save(file_path, creative_file)
                    creatives_ids.append(creative_id)
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=creative_type,
                        file_url=creative_id,
                        uploaded_at=timezone.now(),
                        startup=startup
                    )
                    file_storage.save()
                    logger.info(f"Креатив сохранён с ID: {creative_id}")

            # Сохранение пруфов
            proofs = form.cleaned_data.get('proofs', [])
            if proofs:
                proof_type = FileTypes.objects.get(type_name='proof')
                entity_type = EntityTypes.objects.get(type_name='startup')
                for proof_file in proofs:
                    if not hasattr(proof_file, 'name'):
                        logger.warning(f"Пропущен пруф, так как это не файл: {proof_file}")
                        continue
                    proof_id = str(uuid.uuid4())
                    file_path = f"startups/{startup.startup_id}/proofs/{proof_id}_{proof_file.name}"
                    default_storage.save(file_path, proof_file)
                    proofs_ids.append(proof_id)
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=proof_type,
                        file_url=proof_id,
                        uploaded_at=timezone.now(),
                        startup=startup
                    )
                    file_storage.save()
                    logger.info(f"Пруф сохранён с ID: {proof_id}")

            # Сохранение видео
            video = form.cleaned_data.get('video')
            if video:
                video_id = str(uuid.uuid4())
                file_path = f"startups/{startup.startup_id}/videos/{video_id}_{video.name}"
                default_storage.save(file_path, video)
                video_ids.append(video_id)
                video_type, _ = FileTypes.objects.get_or_create(type_name='video')
                entity_type = EntityTypes.objects.get(type_name='startup')
                file_storage = FileStorage(
                    entity_type=entity_type,
                    entity_id=startup.startup_id,
                    file_type=video_type,
                    file_url=video_id,
                    uploaded_at=timezone.now(),
                    startup=startup
                )
                file_storage.save()
                logger.info(f"Видео сохранено с ID: {video_id}")

            # Сохранение списков ID в поля jsonb
            startup.logo_urls = logo_ids
            startup.creatives_urls = creatives_ids
            startup.proofs_urls = proofs_ids
            startup.video_urls = video_ids
            startup.save()

            # Логирование (оставлено без изменений)
            logger.info("=== Отправка стартапа на модерацию ===")
            logger.info(f"Стартап ID: {startup.startup_id}")
            if logo:
                logger.info(f"Логотип: {logo.name}, размер: {logo.size} байт")
                logger.info(f"ID логотипа: {logo_ids[0] if logo_ids else 'Не сохранён'}")
            else:
                logger.info("Логотип не загружен")
            if creatives:
                logger.info(f"Креативы: {len(creatives)} файлов")
                for i, creative_file in enumerate(creatives, 1):
                    if hasattr(creative_file, 'name'):
                        logger.info(f"Креатив {i}: {creative_file.name}, размер: {creative_file.size} байт")
                    else:
                        logger.info(f"Креатив {i}: Неверный формат (не файл): {creative_file}")
            else:
                logger.info("Креативы не загружены")
            if proofs:
                logger.info(f"Пруфы: {len(proofs)} файлов")
                for i, proof_file in enumerate(proofs, 1):
                    if hasattr(proof_file, 'name'):
                        logger.info(f"Пруф {i}: {proof_file.name}, размер: {proof_file.size} байт")
                    else:
                        logger.info(f"Пруф {i}: Неверный формат (не файл): {proof_file}")
            else:
                logger.info("Пруфы не загружены")
            if video:
                logger.info(f"Видео: {video.name}, размер: {video.size} байт")
                logger.info(f"ID видео: {video_ids[0] if video_ids else 'Не сохранён'}")
            else:
                logger.info("Видео не загружено")
            logger.info("=== Переменные окружения ===")
            for key, value in os.environ.items():
                logger.info(f"{key}: {value}")
            logger.info("=== Настройки Yandex Object Storage ===")
            logger.info(f"AWS_ACCESS_KEY_ID: {getattr(settings, 'AWS_ACCESS_KEY_ID', 'Не задано')}")
            logger.info(f"AWS_SECRET_ACCESS_KEY: {getattr(settings, 'AWS_SECRET_ACCESS_KEY', 'Не задано')}")
            logger.info(f"AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Не задано')}")
            logger.info(f"AWS_S3_ENDPOINT_URL: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'Не задано')}")
            logger.info(f"AWS_DEFAULT_ACL: {getattr(settings, 'AWS_DEFAULT_ACL', 'Не задано')}")
            logger.info("=== Проверка STORAGES ===")
            logger.info(f"STORAGES['default']['BACKEND']: {settings.STORAGES['default']['BACKEND']}")
            logger.info(f"default_storage: {default_storage.__class__.__name__}")
            logger.info("=== Проверка подключения к Yandex Object Storage ===")
            try:
                from storages.backends.s3boto3 import S3Boto3Storage
                from django.core.files.base import ContentFile
                storage = S3Boto3Storage()
                test_file_name = f"test/test_file_{startup.startup_id}.txt"
                test_content = "This is a test file to check Yandex Object Storage connection."
                test_file = ContentFile(test_content.encode('utf-8'))
                storage.save(test_file_name, test_file)
                logger.info(f"Тестовый файл успешно сохранён: {test_file_name}")
                test_file_url = storage.url(test_file_name)
                logger.info(f"URL тестового файла: {test_file_url}")
                storage.delete(test_file_name)
                logger.info(f"Тестовый файл удалён: {test_file_name}")
            except Exception as e:
                logger.error(f"Ошибка подключения к Yandex Object Storage: {str(e)}", exc_info=True)

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
            if 'step_number' in request.POST:
                new_step = int(request.POST.get('step_number'))
                startup.step_number = new_step

            startup.save()

            # Обновление или создание этапов таймлайна
            for i in range(1, 6):
                description = request.POST.get(f'step_description_{i}', '').strip()
                if description:
                    timeline, created = StartupTimeline.objects.get_or_create(
                        startup=startup,
                        step_number=i,
                        defaults={'title': f"Этап {i}", 'description': description}
                    )
                    if not created and timeline.description != description:
                        timeline.description = description
                        timeline.save()

            # Инициализация списков для ID
            logo_ids = startup.logo_urls or []
            creatives_ids = startup.creatives_urls or []
            proofs_ids = startup.proofs_urls or []
            video_ids = startup.video_urls or []

            # Сохранение логотипа
            logo = form.cleaned_data.get('logo')
            if logo:
                logo_id = str(uuid.uuid4())
                file_path = f"startups/{startup.startup_id}/logos/{logo_id}_{logo.name}"
                default_storage.save(file_path, logo)
                logo_ids = [logo_id]
                logger.info(f"Логотип сохранён с ID: {logo_id}")

            # Сохранение креативов
            creatives = form.cleaned_data.get('creatives', [])
            if creatives:
                creative_type = FileTypes.objects.get(type_name='creative')
                entity_type = EntityTypes.objects.get(type_name='startup')
                creatives_ids = []
                for creative_file in creatives:
                    if not hasattr(creative_file, 'name'):
                        logger.warning(f"Пропущен креатив, так как это не файл: {creative_file}")
                        continue
                    creative_id = str(uuid.uuid4())
                    file_path = f"startups/{startup.startup_id}/creatives/{creative_id}_{creative_file.name}"
                    default_storage.save(file_path, creative_file)
                    creatives_ids.append(creative_id)
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=creative_type,
                        file_url=creative_id,
                        uploaded_at=timezone.now(),
                        startup=startup
                    )
                    file_storage.save()
                    logger.info(f"Креатив сохранён с ID: {creative_id}")

            # Сохранение пруфов
            proofs = form.cleaned_data.get('proofs', [])
            if proofs:
                proof_type = FileTypes.objects.get(type_name='proof')
                entity_type = EntityTypes.objects.get(type_name='startup')
                proofs_ids = []
                for proof_file in proofs:
                    if not hasattr(proof_file, 'name'):
                        logger.warning(f"Пропущен пруф, так как это не файл: {proof_file}")
                        continue
                    proof_id = str(uuid.uuid4())
                    file_path = f"startups/{startup.startup_id}/proofs/{proof_id}_{proof_file.name}"
                    default_storage.save(file_path, proof_file)
                    proofs_ids.append(proof_id)
                    file_storage = FileStorage(
                        entity_type=entity_type,
                        entity_id=startup.startup_id,
                        file_type=proof_type,
                        file_url=proof_id,
                        uploaded_at=timezone.now(),
                        startup=startup
                    )
                    file_storage.save()
                    logger.info(f"Пруф сохранён с ID: {proof_id}")

            # Сохранение видео
            video = form.cleaned_data.get('video')
            if video:
                video_id = str(uuid.uuid4())
                file_path = f"startups/{startup.startup_id}/videos/{video_id}_{video.name}"
                default_storage.save(file_path, video)
                video_ids = [video_id]
                video_type, _ = FileTypes.objects.get_or_create(type_name='video')
                entity_type = EntityTypes.objects.get(type_name='startup')
                file_storage = FileStorage(
                    entity_type=entity_type,
                    entity_id=startup.startup_id,
                    file_type=video_type,
                    file_url=video_id,
                    uploaded_at=timezone.now(),
                    startup=startup
                )
                file_storage.save()
                logger.info(f"Видео сохранено с ID: {video_id}")

            # Сохранение списков ID в поля jsonb
            startup.logo_urls = logo_ids
            startup.creatives_urls = creatives_ids
            startup.proofs_urls = proofs_ids
            startup.video_urls = video_ids
            startup.save()

            # Логирование (оставлено без изменений)
            logger.info("=== Обновление стартапа ===")
            logger.info(f"Стартап ID: {startup.startup_id}")
            if logo:
                logger.info(f"Логотип: {logo.name}, размер: {logo.size} байт")
                logger.info(f"ID логотипа: {logo_ids[0] if logo_ids else 'Не сохранён'}")
            else:
                logger.info("Логотип не загружен")
            if creatives:
                logger.info(f"Креативы: {len(creatives)} файлов")
                for i, creative_file in enumerate(creatives, 1):
                    if hasattr(creative_file, 'name'):
                        logger.info(f"Креатив {i}: {creative_file.name}, размер: {creative_file.size} байт")
                    else:
                        logger.info(f"Креатив {i}: Неверный формат (не файл): {creative_file}")
            else:
                logger.info("Креативы не загружены")
            if proofs:
                logger.info(f"Пруфы: {len(proofs)} файлов")
                for i, proof_file in enumerate(proofs, 1):
                    if hasattr(proof_file, 'name'):
                        logger.info(f"Пруф {i}: {proof_file.name}, размер: {proof_file.size} байт")
                    else:
                        logger.info(f"Пруф {i}: Неверный формат (не файл): {proof_file}")
            else:
                logger.info("Пруфы не загружены")
            if video:
                logger.info(f"Видео: {video.name}, размер: {video.size} байт")
                logger.info(f"ID видео: {video_ids[0] if video_ids else 'Не сохранён'}")
            else:
                logger.info("Видео не загружено")
            logger.info("=== Переменные окружения ===")
            for key, value in os.environ.items():
                logger.info(f"{key}: {value}")
            logger.info("=== Настройки Yandex Object Storage ===")
            logger.info(f"AWS_ACCESS_KEY_ID: {getattr(settings, 'AWS_ACCESS_KEY_ID', 'Не задано')}")
            logger.info(f"AWS_SECRET_ACCESS_KEY: {getattr(settings, 'AWS_SECRET_ACCESS_KEY', 'Не задано')}")
            logger.info(f"AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Не задано')}")
            logger.info(f"AWS_S3_ENDPOINT_URL: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'Не задано')}")
            logger.info(f"AWS_DEFAULT_ACL: {getattr(settings, 'AWS_DEFAULT_ACL', 'Не задано')}")
            logger.info("=== Проверка STORAGES ===")
            logger.info(f"STORAGES['default']['BACKEND']: {settings.STORAGES['default']['BACKEND']}")
            logger.info(f"default_storage: {default_storage.__class__.__name__}")
            logger.info("=== Проверка подключения к Yandex Object Storage ===")
            try:
                from storages.backends.s3boto3 import S3Boto3Storage
                from django.core.files.base import ContentFile
                storage = S3Boto3Storage()
                test_file_name = f"test/test_file_{startup.startup_id}.txt"
                test_content = "This is a test file to check Yandex Object Storage connection."
                test_file = ContentFile(test_content.encode('utf-8'))
                storage.save(test_file_name, test_file)
                logger.info(f"Тестовый файл успешно сохранён: {test_file_name}")
                test_file_url = storage.url(test_file_name)
                logger.info(f"URL тестового файла: {test_file_url}")
                storage.delete(test_file_name)
                logger.info(f"Тестовый файл удалён: {test_file_name}")
            except Exception as e:
                logger.error(f"Ошибка подключения к Yandex Object Storage: {str(e)}", exc_info=True)

            messages.success(request, f'Стартап "{startup.title}" успешно отредактирован и отправлен на модерацию!')
            return redirect('profile')
        else:
            messages.error(request, 'Форма содержит ошибки.')
            return render(request, 'accounts/edit_startup.html', {'form': form, 'startup': startup})
    else:
        form = StartupForm(instance=startup)
    return render(request, 'accounts/edit_startup.html', {'form': form, 'startup': startup})

# Панель модератора
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