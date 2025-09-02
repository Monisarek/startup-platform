from django.core.management.base import BaseCommand
from accounts.models import Startups, ReviewStatuses


class Command(BaseCommand):
    help = 'Проверяет статусы всех стартапов'

    def handle(self, *args, **options):
        # Показываем все доступные статусы
        self.stdout.write("=== ДОСТУПНЫЕ СТАТУСЫ ===")
        for status in ReviewStatuses.objects.all():
            self.stdout.write(f"ID: {status.status_id}, Название: {status.status_name}")
        
        self.stdout.write("\n=== СТАТИСТИКА СТАРТАПОВ ===")
        
        # Подсчитываем стартапы по статусам
        status_counts = {}
        for startup in Startups.objects.all():
            status = startup.status
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        for status, count in status_counts.items():
            self.stdout.write(f"Статус '{status}': {count} стартапов")
        
        # Показываем несколько примеров стартапов
        self.stdout.write("\n=== ПРИМЕРЫ СТАРТАПОВ ===")
        for startup in Startups.objects.all()[:10]:
            self.stdout.write(f"ID: {startup.startup_id}, Название: {startup.title}, Статус: {startup.status}")
        
        total_startups = Startups.objects.count()
        approved_startups = Startups.objects.filter(status="approved").count()
        closed_startups = Startups.objects.filter(status="closed").count()
        
        self.stdout.write(f"\n=== ИТОГО ===")
        self.stdout.write(f"Всего стартапов: {total_startups}")
        self.stdout.write(f"Одобренных (approved): {approved_startups}")
        self.stdout.write(f"Закрытых (closed): {closed_startups}")
        
        if approved_startups > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠️  ВНИМАНИЕ: {approved_startups} стартапов все еще имеют статус 'approved'!")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Все стартапы успешно закрыты!")
            )
