from django.core.management.base import BaseCommand
from django.db import connection
from accounts.models import Startups


class Command(BaseCommand):
    help = 'Проверяет подключение к базе данных'

    def handle(self, *args, **options):
        self.stdout.write("=== ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ ===")
        
        # Получаем информацию о подключении
        db_config = connection.settings_dict
        self.stdout.write(f"📊 База данных: {db_config['ENGINE']}")
        self.stdout.write(f"📊 Хост: {db_config.get('HOST', 'localhost')}")
        self.stdout.write(f"📊 Порт: {db_config.get('PORT', '5432')}")
        self.stdout.write(f"📊 Имя БД: {db_config.get('NAME', 'unknown')}")
        
        # Проверяем количество стартапов
        total_startups = Startups.objects.count()
        approved_startups = Startups.objects.filter(status="approved").count()
        closed_startups = Startups.objects.filter(status="closed").count()
        
        self.stdout.write(f"\n📈 Статистика стартапов:")
        self.stdout.write(f"   - Всего стартапов: {total_startups}")
        self.stdout.write(f"   - Одобренных (approved): {approved_startups}")
        self.stdout.write(f"   - Закрытых (closed): {closed_startups}")
        
        # Показываем несколько примеров
        self.stdout.write(f"\n📋 Примеры стартапов:")
        for startup in Startups.objects.all()[:3]:
            self.stdout.write(f"   - {startup.title} (ID: {startup.startup_id}) - статус: {startup.status}")
        
        if approved_startups > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠️  ВНИМАНИЕ: {approved_startups} стартапов имеют статус 'approved'!")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Все стартапы закрыты!")
            )
