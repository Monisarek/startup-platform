from django.core.management.base import BaseCommand
from accounts.models import Startups, ReviewStatuses


class Command(BaseCommand):
    help = 'Переводит все стартапы в статус closed'

    def handle(self, *args, **options):
        try:
            closed_status = ReviewStatuses.objects.get(status_name="Closed")
            self.stdout.write(f"Найден статус 'Closed' с ID: {closed_status.status_id}")
        except ReviewStatuses.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('ОШИБКА: Статус "Closed" не найден в таблице ReviewStatuses')
            )
            return

        startups = Startups.objects.all()
        total_count = startups.count()
        
        if total_count == 0:
            self.stdout.write("Стартапы не найдены")
            return

        self.stdout.write(f"Найдено стартапов: {total_count}")
        
        updated_count = 0
        for startup in startups:
            if startup.status != 'closed':
                startup.status = 'closed'
                startup.status_id = closed_status
                startup.save(update_fields=['status', 'status_id'])
                updated_count += 1
                self.stdout.write(f"Закрыт: {startup.title} (ID: {startup.startup_id})")
            else:
                self.stdout.write(f"Уже закрыт: {startup.title} (ID: {startup.startup_id})")

        self.stdout.write(
            self.style.SUCCESS(f"Операция завершена! Обновлено стартапов: {updated_count}")
        )
