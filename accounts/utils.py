import logging
import uuid
from django.utils import timezone
import requests
import re
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
logger = logging.getLogger(__name__)
def get_file_info(file_id, entity_id, file_type):
    """
    Получает URL и оригинальное имя файла из S3.
    Возвращает словарь с 'url' и 'original_name' или None если файл не найден.
    """
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    if file_type == "avatar":
        prefix = f"users/{entity_id}/avatar/{file_id}_"
    else:
        prefix = f"startups/{entity_id}/{file_type}s/{file_id}_"
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" in response and len(response["Contents"]) > 0:
            key = response["Contents"][0]["Key"]
            url = f"{settings.AWS_S3_ENDPOINT_URL}/{bucket_name}/{key}"
            filename = key.split('/')[-1]
            parts = filename.split('_', 2)
            if len(parts) >= 3:
                original_name = parts[2]
            else:
                original_name = filename
            logger.debug(f"Найден файл {file_type}: {url}, оригинальное имя: {original_name}")
            return {
                'url': url,
                'original_name': original_name
            }
        else:
            logger.warning(f"Файл не найден: prefix={prefix}")
            return None
    except ClientError as e:
        logger.error(f"Ошибка при получении информации о файле: {e}")
        return None
def get_file_url(file_id, entity_id, file_type):
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    if file_type == "avatar":
        prefix = f"users/{entity_id}/avatar/{file_id}_"
    else:
        prefix = f"startups/{entity_id}/{file_type}s/{file_id}_"
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" in response and len(response["Contents"]) > 0:
            key = response["Contents"][0]["Key"]
            url = f"{settings.AWS_S3_ENDPOINT_URL}/{bucket_name}/{key}"
            logger.debug(f"Сгенерирован URL для {file_type}: {url}")
            return url
        else:
            logger.warning(f"Файл не найден: prefix={prefix}")
            return None
    except ClientError as e:
        logger.error(f"Ошибка при генерации URL: {e}")
        return None
def is_uuid(value):
    """
    Проверяет, является ли строка UUID.
    """
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
def get_planet_urls():
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    prefix = "choosable_planets/"
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" not in response:
            logger.warning(f"No files found in {prefix}")
            return []
        planets = [
            obj["Key"].split("/")[-1]
            for obj in response["Contents"]
            if obj["Key"] != prefix
        ]
        return planets
    except ClientError as e:
        logger.error(f"Error listing planets: {e}")
        return []
def update_user_from_telegram(user, sociallogin):
    """
    Forcefully updates a user model instance with data from a Telegram social login account.
    This function compares fields and saves the user only if there are changes.
    First name and last name are intentionally NOT updated to allow user customization.
    """
    if not sociallogin or sociallogin.account.provider != 'telegram':
        return
    try:
        telegram_data = sociallogin.account.extra_data
        update_fields = []
        tg_id = str(telegram_data.get('id'))
        tg_username = telegram_data.get('username')
        tg_photo_url = telegram_data.get('photo_url')
        if user.telegram_id != tg_id:
            user.telegram_id = tg_id
            update_fields.append('telegram_id')
        if tg_username and user.username != tg_username:
            user.username = tg_username
            update_fields.append('username')
        if tg_photo_url and user.profile_picture_url != tg_photo_url:
            user.profile_picture_url = tg_photo_url
            update_fields.append('profile_picture_url')
        if tg_username:
            telegram_handle = f"@{tg_username}"
            if not isinstance(user.social_links, dict) or user.social_links.get('telegram') != telegram_handle:
                if not isinstance(user.social_links, dict):
                    user.social_links = {}
                user.social_links['telegram'] = telegram_handle
                update_fields.append('social_links')
        if update_fields:
            user.updated_at = timezone.now()
            update_fields.append('updated_at')
            user.save(update_fields=update_fields)
            logger.info(f"User {user.username} (ID: {user.pk}) has been updated from Telegram. Fields changed: {update_fields}")
    except Exception as e:
        logger.error(f"CRITICAL ERROR in update_user_from_telegram for user {user.pk}: {e}", exc_info=True)
def escape_markdown_v2(text: str) -> str:
    """Escapes characters for Telegram's MarkdownV2 parse mode."""
    if not text:
        return ''
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def send_telegram_support_message(ticket):
    """
    Sends a formatted support ticket message with an inline button to a specific Telegram chat.
    Uses HTML parse mode for robust formatting.
    """
    bot_token = '7843250850:AAEL8hapR_WVcG2mMNUhWvK-I0DMYG042Ko'
    chat_id = '2064613329'
    
    user = ticket.user
    if not user:
        user_info = "<b>Пользователь:</b> Анонимный"
    else:
        user_full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        user_full_name = user_full_name or "Имя не указано"
        
        email = user.email or "Не указан"
        telegram_handle = user.social_links.get('telegram', 'Не указан') if isinstance(user.social_links, dict) else 'Не указан'

        user_info = (
            f"👤 <b>Пользователь:</b> {user_full_name}\n"
            f"🆔 <b>ID на платформе:</b> <code>{user.user_id}</code>\n"
            f"✉️ <b>Email:</b> <code>{email}</code>\n"
            f"✈️ <b>Telegram:</b> {telegram_handle}"
        )

    subject = f"<pre>{ticket.subject}</pre>"
    message = f"<pre>{ticket.message}</pre>"

    message_text = (
        f"🚨 <b>Новая заявка в техподдержку ({ticket.ticket_id})</b> 🚨\n\n"
        f"📝 <b>Тема:</b>\n{subject}\n\n"
        f"📄 <b>Сообщение:</b>\n{message}\n\n"
        f"--- Техническая информация ---\n"
        f"{user_info}"
    )

    inline_keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Исполнено", "callback_data": f"close_ticket_{ticket.ticket_id}"}
        ]]
    }

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message_text,
        'parse_mode': 'HTML',
        'reply_markup': inline_keyboard
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully sent support ticket {ticket.ticket_id} to Telegram chat {chat_id}.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send support ticket {ticket.ticket_id} to Telegram: {e}", exc_info=True)
        return False
