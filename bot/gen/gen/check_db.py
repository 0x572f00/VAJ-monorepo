#!/usr/bin/env python3
"""
Скрипт для проверки содержимого базы данных
"""

import sqlite3
import os

def check_database():
    db_path = 'bot_database.db'
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 Проверка базы данных:")
    print("=" * 50)
    
    # Проверяем таблицу администраторов
    print("\n👥 Администраторы:")
    cursor.execute('SELECT user_id, username, added_date FROM admins')
    admins = cursor.fetchall()
    if admins:
        for admin in admins:
            print(f"  • {admin[1]} (ID: {admin[0]}) - {admin[2]}")
    else:
        print("  Нет администраторов")
    
    # Проверяем таблицу случайных изображений
    print("\n📸 Случайные изображения:")
    cursor.execute('SELECT id, file_id, file_path, added_date FROM random_images')
    images = cursor.fetchall()
    if images:
        for img in images:
            filename = os.path.basename(img[2])
            print(f"  • {filename} (ID: {img[0]}) - {img[3]}")
        print(f"\n  Всего изображений: {len(images)}")
    else:
        print("  Нет изображений")
    
    # Проверяем таблицу пользователей
    print("\n👤 Пользователи:")
    cursor.execute('SELECT user_id, username FROM users')
    users = cursor.fetchall()
    if users:
        for user in users:
            print(f"  • {user[1]} (ID: {user[0]})")
        print(f"\n  Всего пользователей: {len(users)}")
    else:
        print("  Нет пользователей")
    
    conn.close()

if __name__ == "__main__":
    check_database() 