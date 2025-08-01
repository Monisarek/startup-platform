import json
from django import template
from django.utils.safestring import mark_safe
from allauth.socialaccount.templatetags.socialaccount import provider_login_url as allauth_provider_login_url
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
register = template.Library()
@register.filter(name="translate_category")
def translate_category(name):
    """Переводит английское название категории на русский."""
    translations = {
        "Medicine": "Медицина",
        "Auto": "Автомобили",
        "Delivery": "Доставка",
        "Cafe": "Кафе/рестораны",
        "Fastfood": "Фастфуд",
        "Health": "Здоровье",
        "Beauty": "Красота",
        "Transport": "Транспорт",
        "Sport": "Спорт",
        "Psychology": "Психология",
        "AI": "ИИ",
        "Finance": "Финансы",
        "Healthcare": "Здравоохранение",
        "Technology": "Технологии",
    }
    return translations.get(
        name, name if name else "Без категории"
    )


@register.simple_tag
def multiply(qty, unit_price, *args, **kwargs):
    return qty * unit_price


@register.filter(name="get_file_url")
def get_file_url(file_id, entity_id, file_type):
    return "#"


@register.filter(name="jsonify")
def jsonify(data):
    return mark_safe(json.dumps(data))


@register.filter(name="startswith")
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter(name="has_invested")
def has_invested(user, startup):
    return False


@register.filter(name="is_buyout_investor")
def is_buyout_investor(user, startup):
    return True



@register.filter(name="get_item")
def get_item(dictionary, key):
    """Позволяет получить значение из словаря по ключу в шаблоне Django."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return 0
@register.filter(is_safe=True, name="to_json")
def to_json(value):
    try:
        json_string = json.dumps(value)
        return mark_safe(json_string)
    except TypeError:
        return mark_safe("null")
@register.simple_tag(takes_context=True)
def get_telegram_login_url(context):
    """
    Генерирует URL для входа через Telegram, принудительно используя 'www' в домене.
    """
    request = context.get('request')
    if not request:
        return '#'
    original_url = allauth_provider_login_url(context, 'telegram')
    parsed_url = urlparse(original_url)
    query_params = parse_qs(parsed_url.query)
    for param_name in ['origin', 'return_to']:
        if param_name in query_params and query_params[param_name]:
            inner_url_str = query_params[param_name][0]
            if '://greatideas.ru' in inner_url_str:
                new_inner_url = inner_url_str.replace('://greatideas.ru', '://www.greatideas.ru')
                query_params[param_name][0] = new_inner_url
    new_query_string = urlencode(query_params, doseq=True)
    new_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, new_query_string, parsed_url.fragment)
    )
    return new_url
