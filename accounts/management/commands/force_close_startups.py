from django.core.management.base import BaseCommand
from accounts.models import Startups, ReviewStatuses


class Command(BaseCommand):
    help = 'Принудительно закрывает все стартапы'

    def handle(self, *args, **options):
        self.stdout.write("=== ПРИНУДИТЕЛЬНОЕ ЗАКРЫТИЕ ВСЕХ СТАРТАПОВ ===")
        
        try:
            closed_status = ReviewStatuses.objects.get(status_name="Closed")
            self.stdout.write(f"✅ Найден статус 'Closed' с ID: {closed_status.status_id}")
        except ReviewStatuses.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ ОШИБКА: Статус "Closed" не найден в таблице ReviewStatuses')
            )
            return

        startups = Startups.objects.all()
        total_count = startups.count()
        
        if total_count == 0:
            self.stdout.write("ℹ️  Стартапы не найдены")
            return

        self.stdout.write(f"📊 Найдено стартапов: {total_count}")
        
        # Показываем текущие статусы
        status_counts = {}
        for startup in startups:
            status = startup.status
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        self.stdout.write("📈 Текущие статусы:")
        for status, count in status_counts.items():
            self.stdout.write(f"   - {status}: {count} стартапов")
        
        # Принудительно закрываем все стартапы
        self.stdout.write("\n🔄 Начинаем принудительное закрытие...")
        updated_count = 0
        for startup in startups:
            old_status = startup.status
            startup.status = 'closed'
            startup.status_id = closed_status
            startup.save(update_fields=['status', 'status_id'])
            updated_count += 1
            self.stdout.write(f"   ✅ {startup.title} (ID: {startup.startup_id}) - {old_status} → closed")

        self.stdout.write(f"\n🎉 Операция завершена! Обновлено стартапов: {updated_count}")
        
        # Проверяем результат
        approved_count = Startups.objects.filter(status="approved").count()
        closed_count = Startups.objects.filter(status="closed").count()
        self.stdout.write(f"\n📊 Итоговая проверка:")
        self.stdout.write(f"   - Одобренных (approved): {approved_count}")
        self.stdout.write(f"   - Закрытых (closed): {closed_count}")
        
        if approved_count > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠️  ВНИМАНИЕ: {approved_count} стартапов все еще имеют статус 'approved'!")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Все стартапы успешно закрыты!")
            )
