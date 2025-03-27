# accounts/utils.py
import uuid
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

def get_file_url(file_id, startup_id, file_type):
    """
    Генерирует URL для файла на основе его ID, ID стартапа и типа файла.
    file_id: уникальный ID файла (хранится в FileStorage.file_url)
    startup_id: ID стартапа
    file_type: 'logo', 'creative', 'proof' или 'video'
    """
    # Создаём клиент для Yandex Object Storage
    s3_client = boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    # Определяем путь к файлу в Yandex Object Storage
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    prefix = f"startups/{startup_id}/{file_type}s/{file_id}_"
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response and len(response['Contents']) > 0:
            key = response['Contents'][0]['Key']
            # Генерируем URL (публичный или подписанный)
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': key
                },
                ExpiresIn=3600  # URL действителен 1 час
            )
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