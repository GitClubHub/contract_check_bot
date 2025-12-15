import requests
import json
from config import YC_API_KEY, YC_FOLDER_ID, YC_AGENT_ID

class YandexAgent:
    def __init__(self):
        self.api_url = f"https://agent.llm.api.cloud.yandex.net/llm/v2/folders/{YC_FOLDER_ID}/agents/{YC_AGENT_ID}:chat"
        self.headers = {
            "Authorization": f"Api-Key {YC_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def analyze_contract(self, text):
        """Анализирует текст договора"""
        
        # Обрезаем очень длинные тексты
        if len(text) > 100000:
            text = text[:100000] + "\n\n[Текст обрезан из-за длины]"
        
        prompt = f"""
Проанализируй этот договор как юрист. Выдели:
1. Основные риски (высокий/средний/низкий)
2. Подозрительные условия
3. Что нужно уточнить у второй стороны

Договор:
{text}

Ответь кратко и по делу.
"""
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "generationOptions": {
                "maxTokens": 2000,
                "temperature": 0.1
            }
        }
        
        try:
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                # Структура ответа может отличаться - нужно проверить
                return result.get('message', {}).get('content', 'Не удалось получить ответ')
            else:
                return f"Ошибка API: {response.status_code}"
                
        except Exception as e:
            return f"Ошибка соединения: {str(e)}"
