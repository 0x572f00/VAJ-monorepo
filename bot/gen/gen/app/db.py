import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        with self.connection:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
            """)
            
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                added_date TEXT NOT NULL
            )
            """)
            
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS random_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                added_date TEXT NOT NULL
            )
            """)

    async def check_user_exists(self, user_id):
        with self.connection:
            self.cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            return self.cursor.fetchone() is not None

    async def add_user(self, user_id, username):
        if await self.check_user_exists(user_id):
            return False
        with self.connection:
            self.cursor.execute(
                '''INSERT INTO users (user_id, username)
                   VALUES (?, ?)''',
                (user_id, username)
            )
            self.connection.commit()
            return True

    async def add_admin(self, user_id, username):
        """Добавить администратора"""
        with self.connection:
            self.cursor.execute(
                '''INSERT OR REPLACE INTO admins (user_id, username, added_date)
                   VALUES (?, ?, datetime('now'))''',
                (user_id, username)
            )
            self.connection.commit()
            return True

    async def remove_admin(self, user_id):
        """Удалить администратора"""
        with self.connection:
            self.cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0

    async def get_all_admins(self):
        """Получить всех администраторов"""
        with self.connection:
            self.cursor.execute('SELECT user_id, username, added_date FROM admins')
            return self.cursor.fetchall()

    async def is_admin(self, user_id):
        """Проверить, является ли пользователь администратором"""
        with self.connection:
            self.cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            return self.cursor.fetchone() is not None

    async def add_random_image(self, file_id, file_path):
        """Добавить случайное изображение"""
        with self.connection:
            self.cursor.execute(
                '''INSERT INTO random_images (file_id, file_path, added_date)
                   VALUES (?, ?, datetime('now'))''',
                (file_id, file_path)
            )
            self.connection.commit()
            return True

    async def remove_random_image(self, image_id):
        """Удалить случайное изображение по ID"""
        with self.connection:
            self.cursor.execute('SELECT file_path FROM random_images WHERE id = ?', (image_id,))
            result = self.cursor.fetchone()
            if result:
                file_path = result[0]
                self.cursor.execute('DELETE FROM random_images WHERE id = ?', (image_id,))
                self.connection.commit()
                return file_path
            return None

    async def get_all_random_images(self):
        """Получить все случайные изображения"""
        with self.connection:
            self.cursor.execute('SELECT id, file_id, file_path, added_date FROM random_images ORDER BY id')
            return self.cursor.fetchall()

    async def get_random_image(self):
        """Получить случайное изображение"""
        with self.connection:
            self.cursor.execute('SELECT file_id, file_path FROM random_images ORDER BY RANDOM() LIMIT 1')
            return self.cursor.fetchone()