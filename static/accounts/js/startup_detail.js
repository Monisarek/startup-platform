document.addEventListener('DOMContentLoaded', function() {
    const stars = document.querySelectorAll('.star');
    const startupId = parseInt(document.querySelector('input[name="startup_id"]').value, 10) || 0; // Получаем startup_id из скрытого поля

    // Проверяем, есть ли звезды и startupId
    if (!stars.length || !startupId) {
        console.error('Ошибка: звезды не найдены или startupId отсутствует');
        return;
    }

    stars.forEach(star => {
        // Наведение на звезду
        star.addEventListener('mouseover', function() {
            const value = parseInt(this.getAttribute('data-value'), 10);
            stars.forEach(s => {
                const sValue = parseInt(s.getAttribute('data-value'), 10);
                s.classList.toggle('filled', sValue <= value);
            });
        });

        // Уход курсора
        star.addEventListener('mouseout', function() {
            const averageRating = parseFloat(document.querySelector('input[name="average_rating"]').value) || 0; // Получаем из скрытого поля
            stars.forEach(s => {
                const sValue = parseInt(s.getAttribute('data-value'), 10);
                s.classList.toggle('filled', sValue <= Math.floor(averageRating));
            });
        });

        // Клик по звезде
        star.addEventListener('click', function() {
            const value = parseInt(this.getAttribute('data-value'), 10);
            fetch(`/vote_startup/${startupId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value
                },
                body: JSON.stringify({ rating: value })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка сети: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const averageRating = parseFloat(data.average_rating) || 0;
                    stars.forEach(s => {
                        const sValue = parseInt(s.getAttribute('data-value'), 10);
                        s.classList.toggle('filled', sValue <= Math.floor(averageRating));
                    });
                } else {
                    alert(data.error || 'Ошибка при голосовании');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error.message);
            });
        });
    });
});