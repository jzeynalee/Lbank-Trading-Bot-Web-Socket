
import sqlite3

class SignalDatabase:
    def __init__(self, db_path="signals.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            interval TEXT,
            timestamp TEXT,
            price REAL,
            signal TEXT
        );
        '''
        self.conn.execute(query)
        self.conn.commit()

    def save_signal(self, symbol, interval, timestamp, price, signal):
        query = "INSERT INTO signals (symbol, interval, timestamp, price, signal) VALUES (?, ?, ?, ?, ?)"
        self.conn.execute(query, (symbol, interval, timestamp, price, signal))
        self.conn.commit()

    def get_signals(self, limit=100):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?", (limit,))
        return cursor.fetchall()
