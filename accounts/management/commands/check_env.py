from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = 'Показывает переменные окружения'

    def handle(self, *args, **options):
        self.stdout.write("=== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===")
        
        # Показываем важные переменные
        important_vars = [
            'DATABASE_URL',
            'DJANGO_DEBUG',
            'DJANGO_SECRET_KEY',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_STORAGE_BUCKET_NAME',
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_OWNER_CHAT_ID'
        ]
        
        for var in important_vars:
            value = os.getenv(var, 'НЕ УСТАНОВЛЕНА')
            if var == 'DATABASE_URL' and value != 'НЕ УСТАНОВЛЕНА':
                # Скрываем пароль в DATABASE_URL
                if '@' in value:
                    parts = value.split('@')
                    if len(parts) == 2:
                        user_pass = parts[0].split('//')[-1]
                        if ':' in user_pass:
                            user = user_pass.split(':')[0]
                            value = value.replace(user_pass, f"{user}:***")
            self.stdout.write(f"📊 {var}: {value}")
        
        # Показываем все переменные, содержащие DATABASE
        self.stdout.write(f"\n📊 Все переменные с 'DATABASE':")
        for key, value in os.environ.items():
            if 'DATABASE' in key.upper():
                if 'URL' in key.upper() and '@' in value:
                    # Скрываем пароль
                    parts = value.split('@')
                    if len(parts) == 2:
                        user_pass = parts[0].split('//')[-1]
                        if ':' in user_pass:
                            user = user_pass.split(':')[0]
                            value = value.replace(user_pass, f"{user}:***")
                self.stdout.write(f"   - {key}: {value}")
        
        # Показываем все переменные, содержащие RENDER
        self.stdout.write(f"\n📊 Все переменные с 'RENDER':")
        for key, value in os.environ.items():
            if 'RENDER' in key.upper():
                self.stdout.write(f"   - {key}: {value}")
        
        # Показываем все переменные, содержащие POSTGRES
        self.stdout.write(f"\n📊 Все переменные с 'POSTGRES':")
        for key, value in os.environ.items():
            if 'POSTGRES' in key.upper():
                self.stdout.write(f"   - {key}: {value}")
