# config.py - ПРОСТАЯ ВЕРСИЯ БЕЗ DOTENV

# 1. ТОКЕН БОТА ОТ @BOTFATHER
BOT_TOKEN = "6123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"

# 2. ДАННЫЕ ОТ ЯНДЕКС ОБЛАКА
YC_API_KEY = "AQVN1UmjsC7q7KXhTz5R2x1yY9Z8W4BcDeFgH"  # Ваш API-ключ
YC_FOLDER_ID = "b1g9ma2ql6hex5c3pd4q"                 # ID каталога
YC_AGENT_ID = "9f8e7d6c-5b4a-3v2g-1h0i-j1k2l3m4n5o6"  # ID агента

# 3. НАСТРОЙКИ
FREE_CHECKS = 1
PRICE_PER_CHECK = 299
MAX_FILE_SIZE_MB = 20
SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt']

# URL для API агента (автоматически соберется)
AGENT_API_URL = f"https://agent.llm.api.cloud.yandex.net/llm/v2/folders/{YC_FOLDER_ID}/agents/{YC_AGENT_ID}:chat"
