from django.core.management.base import BaseCommand
from accounts.models import Startups, ReviewStatuses


class Command(BaseCommand):
    help = 'Закрывает все стартапы в продакшн базе'

    def handle(self, *args, **options):
        self.stdout.write("=== ЗАКРЫТИЕ СТАРТАПОВ В ПРОДАКШН БАЗЕ ===")
        
        try:
            # Получаем статус "Closed"
            closed_status = ReviewStatuses.objects.get(status_name="Closed")
            self.stdout.write(f"✅ Найден статус 'Closed' с ID: {closed_status.status_id}")
        except ReviewStatuses.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ ОШИБКА: Статус "Closed" не найден в таблице ReviewStatuses')
            )
            return

        # Получаем все стартапы
        startups = Startups.objects.all()
        total_count = startups.count()
        
        if total_count == 0:
            self.stdout.write("ℹ️  Стартапы не найдены")
            return

        self.stdout.write(f"📊 Найдено стартапов в продакшн базе: {total_count}")
        
        # Показываем текущие статусы
        status_counts = {}
        for startup in startups:
            status = startup.status
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        self.stdout.write("📈 Текущие статусы в продакшн базе:")
        for status, count in status_counts.items():
            self.stdout.write(f"   - {status}: {count} стартапов")
        
        # Показываем несколько примеров
        self.stdout.write("\n📋 Примеры стартапов:")
        for startup in startups[:5]:
            self.stdout.write(f"   - {startup.title} (ID: {startup.startup_id}) - статус: {startup.status}")
        
        # Закрываем все стартапы
        self.stdout.write(f"\n🔄 Начинаем закрытие {total_count} стартапов...")
        updated_count = 0
        for startup in startups:
            old_status = startup.status
            startup.status = 'closed'
            startup.status_id = closed_status
            startup.save(update_fields=['status', 'status_id'])
            updated_count += 1
            if updated_count <= 10:  # Показываем первые 10
                self.stdout.write(f"   ✅ {startup.title} (ID: {startup.startup_id}) - {old_status} → closed")
            elif updated_count == 11:
                self.stdout.write("   ... (остальные стартапы закрываются)")

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
                self.style.SUCCESS("✅ Все стартапы успешно закрыты в продакшн базе!")
            )
