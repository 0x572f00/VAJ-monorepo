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