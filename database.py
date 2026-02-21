import sqlite3
from datetime import datetime

DB_FILE = "production.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        worker_id TEXT,
        fio TEXT,
        otdel TEXT,
        product TEXT,
        category TEXT,
        quantity_pieces REAL,
        caliber_kg REAL,
        quantity_kg REAL,
        salary_coeff REAL,
        daily_salary INTEGER,
        full_salary INTEGER,
        reduced_amount INTEGER,
        percent_complete REAL,
        total_points INTEGER,
        bonus_percent INTEGER,
        source TEXT DEFAULT 'Вручную'
    )''')
    conn.commit()
    conn.close()

def add_record(record):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO records (
        date, worker_id, fio, otdel, product, category,
        quantity_pieces, caliber_kg, quantity_kg,
        salary_coeff, daily_salary, full_salary, reduced_amount,
        percent_complete, total_points, bonus_percent, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (record['date'], record['worker_id'], record['fio'], record['otdel'],
     record['product'], record['category'],
     record.get('quantity_pieces', 0), record.get('caliber_kg', 0), record['quantity_kg'],
     record.get('salary_coeff', 1.0), record['daily_salary'], record['full_salary'],
     record.get('reduced_amount', 0),
     record.get('percent_complete', 0), record.get('total_points', 0),
     record.get('bonus_percent', 0), record.get('source', 'Вручную')))
    conn.commit()
    conn.close()

def get_all_records():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM records ORDER BY date DESC")
    rows = c.fetchall()
    conn.close()
    columns = [desc[0] for desc in c.description]
    return [dict(zip(columns, row)) for row in rows]

def get_records_by_date(target_date):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM records WHERE date = ? ORDER BY id DESC", (target_date,))
    rows = c.fetchall()
    conn.close()
    columns = [desc[0] for desc in c.description]
    return [dict(zip(columns, row)) for row in rows]
