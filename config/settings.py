import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Yandex Cloud
    YC_FOLDER_ID = os.getenv("YC_FOLDER_ID")
    YC_AGENT_ID = os.getenv("YC_AGENT_ID")
    YC_IAM_TOKEN = os.getenv("YC_IAM_TOKEN")
    YC_API_KEY = os.getenv("YC_API_KEY")
    
    # Agent API
    AGENT_API_URL = f"https://agent.llm.api.cloud.yandex.net/llm/v2/folders/{YC_FOLDER_ID}/agents/{YC_AGENT_ID}:chat"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/contracts.db")
    
    # Payment
    YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
    YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
    
    # Prices
    FREE_CHECKS = int(os.getenv("FREE_CHECKS", 1))
    SINGLE_CHECK_PRICE = int(os.getenv("SINGLE_CHECK_PRICE", 299))
    SUBSCRIPTION_PRICE = int(os.getenv("SUBSCRIPTION_PRICE", 999))
    
    # Limits
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 20)) * 1024 * 1024
    MAX_TEXT_LENGTH = 100000  # символов
    
    # Paths
    TEMP_DIR = "temp"
    LOG_FILE = "bot.log"

config = Config()
