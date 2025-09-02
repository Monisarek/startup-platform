from django.core.management.base import BaseCommand
from accounts.models import Startups, ReviewStatuses


class Command(BaseCommand):
    help = 'Закрывает стартапы точно так же, как ручное изменение статуса'

    def handle(self, *args, **options):
        self.stdout.write("=== РУЧНОЕ ЗАКРЫТИЕ СТАРТАПОВ ===")
        
        # Получаем статус "Closed" точно так же, как в views.py
        try:
            closed_status = ReviewStatuses.objects.get(status_name="Closed")
            self.stdout.write(f"✅ Найден статус 'Closed' с ID: {closed_status.status_id}")
        except ReviewStatuses.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ ОШИБКА: Статус "Closed" не найден')
            )
            return

        # Получаем все стартапы
        startups = Startups.objects.all()
        total_count = startups.count()
        
        if total_count == 0:
            self.stdout.write("ℹ️  Стартапы не найдены")
            return

        self.stdout.write(f"📊 Найдено стартапов: {total_count}")
        
        # Закрываем стартапы точно так же, как в startup_detail view
        updated_count = 0
        for startup in startups:
            # Точно такая же логика, как в views.py строка 2053-2065
            startup.status = 'closed'
            startup.status_id = closed_status
            startup.save(update_fields=['status', 'status_id'])
            updated_count += 1
            self.stdout.write(f"✅ Закрыт: {startup.title} (ID: {startup.startup_id})")

        self.stdout.write(f"\n🎉 Закрыто стартапов: {updated_count}")
        
        # Проверяем результат
        approved_count = Startups.objects.filter(status="approved").count()
        closed_count = Startups.objects.filter(status="closed").count()
        self.stdout.write(f"📊 Результат: approved={approved_count}, closed={closed_count}")
        
        if approved_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ Все стартапы закрыты!"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  {approved_count} стартапов все еще approved"))
