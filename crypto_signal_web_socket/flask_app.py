from flask import Flask, render_template, jsonify
import sqlite3
from my_modules.db.signal_db import SignalDatabase

app = Flask(__name__)
SignalDatabase()  # Ensure table exists

DB_PATH = 'signals.db'

def get_signals():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 50")
    data = cursor.fetchall()
    conn.close()
    return data

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/signals')
def api_signals():
    data = get_signals()
    return jsonify([
        {
            "symbol": row[1],
            "interval": row[2],
            "timestamp": row[3],
            "price": row[4],
            "signal": row[5]
        }
        for row in data
    ])

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
