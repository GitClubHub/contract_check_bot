"""
database.py - Простая база данных SQLite
"""

import sqlite3
import os

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Пользователи
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            checks_used INTEGER DEFAULT 0,
            last_check_time TIMESTAMP
        )
    ''')
    
    # История проверок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user_checks(user_id):
    """Получить количество использованных проверок"""
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT checks_used FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if not result:
        cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        checks_used = 0
    else:
        checks_used = result[0]
    
    conn.close()
    return checks_used

def add_user_check(user_id, filename, result):
    """Добавить проверку в историю"""
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Добавляем запись о проверке
    cursor.execute('''
        INSERT INTO checks (user_id, filename, result) 
        VALUES (?, ?, ?)
    ''', (user_id, filename, result[:500]))  # Сохраняем только начало
    
    # Обновляем счетчик
    cursor.execute('''
        UPDATE users 
        SET checks_used = checks_used + 1,
            last_check_time = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()

# Инициализируем БД при импорте
if not os.path.exists('bot.db'):
    init_db()
