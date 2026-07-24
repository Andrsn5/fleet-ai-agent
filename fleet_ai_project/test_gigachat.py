import sys
from gigachat import GigaChat

# Принудительно заставляем консоль Windows понимать русский язык
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Вставь сюда свой длинный ключ из кабинета разработчика (Base64)
MY_CREDENTIALS = "MDE5ZjkwZTUtYjE5YS03MDc3LThkZmEtYWVhMzI1YTFmNDZhOmNhODg5YTkwLTZjZjktNDUwYS1hOWRlLWUzYThkMDY3MjUzYQ=="

try:
    print("Пробуем подключиться к GigaChat...")
    with GigaChat(credentials=MY_CREDENTIALS, verify_ssl_certs=False, scope="GIGACHAT_API_PERS") as giga:
        response = giga.chat("Привет! Скажи слово 'Успех', если слышишь меня.")
        print("\nОТВЕТ ПОЛУЧЕН:")
        print(response.choices[0].message.content)
except Exception as e:
    print("\nОШИБКА АВТОРИЗАЦИИ:")
    print(e)