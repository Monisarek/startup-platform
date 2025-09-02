set -o errexit

echo "--- Installing Python dependencies ---"
pip install -r requirements.txt

echo "--- Installing JS dependencies ---"
npm install

echo "--- Building frontend ---"
npm run build

echo "--- VITE MANIFEST CONTENT ---"
cat static/dist/.vite/manifest.json || echo "Manifest file not found"
echo "--- END VITE MANIFEST CONTENT ---"

echo "--- Applying database migrations ---"
echo "--- Prechecking migration consistency for accounts app ---"
python - <<'PY'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
try:
    import django
    django.setup()
    from django.db import connection
    from django.db.migrations.recorder import MigrationRecorder

    tables = set(connection.introspection.table_names())
    applied = {name for app, name in MigrationRecorder(connection).applied_migrations() if app == 'accounts'}

    def run(cmd):
        import subprocess, shlex
        print(f"[precheck] $ {cmd}")
        subprocess.run(shlex.split(cmd), check=False)

    if '0036_create_agencies' not in applied and 'agencies' in tables:
        run('python manage.py migrate accounts 0036_create_agencies --fake')

    if '0037_agency_feedback' not in applied and {'agency_votes','agency_comments'}.issubset(tables):
        run('python manage.py migrate accounts 0037_agency_feedback --fake')
except Exception as e:
    print(f"[precheck] skipped due to error: {e}")
PY

python manage.py migrate --noinput

echo "--- Closing all startups ---"
/opt/render/project/src/.venv/bin/python - <<'PY'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
try:
    import django
    django.setup()
    from accounts.models import Startups, ReviewStatuses
    
    print("=== ЗАКРЫТИЕ ВСЕХ СТАРТАПОВ ===")
    
    # Получаем статус "Closed"
    try:
        closed_status = ReviewStatuses.objects.get(status_name="Closed")
        print(f"Найден статус 'Closed' с ID: {closed_status.status_id}")
    except ReviewStatuses.DoesNotExist:
        print("ОШИБКА: Статус 'Closed' не найден в таблице ReviewStatuses")
        exit(1)
    
    # Получаем все стартапы
    startups = Startups.objects.all()
    total_count = startups.count()
    
    if total_count == 0:
        print("Стартапы не найдены")
        exit(0)
    
    print(f"Найдено стартапов: {total_count}")
    
    # Закрываем все стартапы
    updated_count = 0
    for startup in startups:
        startup.status = 'closed'
        startup.status_id = closed_status
        startup.save(update_fields=['status', 'status_id'])
        updated_count += 1
        print(f"Закрыт: {startup.title} (ID: {startup.startup_id})")
    
    print(f"Операция завершена! Обновлено стартапов: {updated_count}")
    
    # Проверяем результат
    approved_count = Startups.objects.filter(status="approved").count()
    closed_count = Startups.objects.filter(status="closed").count()
    print(f"Проверка: одобренных - {approved_count}, закрытых - {closed_count}")
    
    if approved_count > 0:
        print(f"⚠️  ВНИМАНИЕ: {approved_count} стартапов все еще имеют статус 'approved'!")
    else:
        print("✅ Все стартапы успешно закрыты!")
        
except Exception as e:
    print(f"ОШИБКА при закрытии стартапов: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
PY

echo "--- Collecting static files ---"

/opt/render/project/src/.venv/bin/python manage.py collectstatic --noinput --clear

echo "--- Build successful ---"
