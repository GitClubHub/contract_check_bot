import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Получить у @BotFather
YC_API_KEY = os.getenv("YC_API_KEY")  # Ключ от Яндекс Облака
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID")  # ID каталога в Яндекс Облаке
YC_AGENT_ID = os.getenv("YC_AGENT_ID")  # ID вашего агента

# Цены
FREE_CHECKS = 1
PRICE_PER_CHECK = 299

# Лимиты
MAX_FILE_SIZE_MB = 20
SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt']
