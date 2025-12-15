import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # Пользователи
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            free_checks_used INTEGER DEFAULT 0,
            paid_checks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Проверки
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            analysis_result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        user = (user_id, 0, 0, datetime.now())
    
    conn.close()
    return {
        'user_id': user[0],
        'free_checks_used': user[1],
        'paid_checks': user[2]
    }

def add_check(user_id, filename, result):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO checks (user_id, filename, analysis_result)
        VALUES (?, ?, ?)
    ''', (user_id, filename, result))
    
    # Увеличиваем счетчик проверок
    cursor.execute('''
        UPDATE users 
        SET free_checks_used = free_checks_used + 1 
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    return cursor.lastrowid

# Инициализируем БД при импорте
init_db()
