from flask import Flask, jsonify
import os
import mysql.connector

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.getenv('DB_USER', 'appuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'changeme')
DB_NAME = os.getenv('DB_NAME', 'appdb')

@app.get('/api/health')

def health():
    return {'status': 'ok'}

@app.get('/api')

def index():
    """Simple endpoint that greets from DB."""
    conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    )
    cur = conn.cursor()
    cur.execute("SELECT 'Hello from MySQL via Flask!'")
    row = cur.fetchone()
    cur.close(); conn.close()
    return jsonify(message=row[0])

if __name__ == '__main__':
    # Dev-only fallback
    app.run(host='0.0.0.0', port=8000, debug=True)