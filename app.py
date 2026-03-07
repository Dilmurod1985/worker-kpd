import os
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "dilmurat_group_system_2026"

# Определяем путь к папке проекта
basedir = os.path.abspath(os.path.dirname(__file__))

# === УЛЬТРА-СТАБИЛЬНЫЙ БЛОК БАЗЫ ДАННЫХ ===
database_url = os.environ.get('DATABASE_URL')

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "connect_args": {
            "sslmode": "require",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'production.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# === МОДЕЛИ ДАННЫХ ===
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.String(20), unique=True)
    fio = db.Column(db.String(100))
    category = db.Column(db.String(50))

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.String(20))
    date = db.Column(db.String(20))
    otdel = db.Column(db.String(100))
    total_kpd = db.Column(db.Float)
    kalibr = db.Column(db.Float)
    sht = db.Column(db.Float)
    shift = db.Column(db.String(20))

# Инициализация базы
with app.app_context():
    db.create_all()

# === МАРШРУТЫ (ROUTES) ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/workers', methods=['GET', 'POST'])
def workers():
    if request.method == 'POST':
        data = request.form.get('bulk_workers', '')
        for line in data.strip().split('\n'):
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                wid = parts[0].strip()
                if not Worker.query.filter_by(worker_id=wid).first():
                    db.session.add(Worker(worker_id=wid, fio=parts[1].strip(), 
                                        category=parts[2].strip() if len(parts)>2 else "5"))
        db.session.commit()
    return render_template('workers.html', workers=Worker.query.all())

@app.route('/delete_worker/<int:id>')
def delete_worker(id):
    w = Worker.query.get(id)
    if w:
        db.session.delete(w)
        db.session.commit()
    return redirect(url_for('workers'))

@app.route('/bulk_input', methods=['POST'])
def bulk_input():
    data = request.form.get('bulk_data', '')
    date_str = request.form.get('date', '')
    for line in data.strip().split('\n'):
        p = line.split()
        if len(p) >= 5:
            wid = p[0].strip()
            if Worker.query.filter_by(worker_id=wid).first():
                try:
                    db.session.add(Record(
                        worker_id=wid, date=date_str, otdel=p[1],
                        total_kpd=float(p[2].replace(',', '.')), 
                        kalibr=float(p[3].replace(',', '.')), 
                        sht=float(p[4].replace(',', '.')), 
                        shift=p[5] if len(p) > 5 else "Ночь"
                    ))
                except: continue
    db.session.commit()
    return redirect(url_for('tabel'))

@app.route('/tabel')
def tabel():
    records = Record.query.all()
    norms = {"1": 300, "2": 280, "3": 250, "4": 220, "5": 100}
    grouped = {}
    for r in records:
        key = (r.date, r.shift, r.worker_id)
        if key not in grouped:
            grouped[key] = {
                'date': r.date, 'id': r.worker_id, 'pos': [r.otdel],
                'kalibr': r.kalibr, 'sht': r.sht, 'summa': r.total_kpd, 'shift': r.shift
            }
        else:
            if r.otdel not in grouped[key]['pos']:
                grouped[key]['pos'].append(r.otdel)
            grouped[key]['summa'] += r.total_kpd
            grouped[key]['sht'] += r.sht
    
    rows = []
    for data in grouped.values():
        w = Worker.query.filter_by(worker_id=data['id']).first()
        cat_num = "".join(filter(str.isdigit, w.category)) if w else "5"
        norm_val = norms.get(cat_num, 100)
        percent = (data['summa'] / norm_val * 100) if norm_val > 0 else 0
        rows.append({
            'date': data['date'], 'id': data['id'], 'fio': w.fio if w else "-",
            'cat': w.category if w else "-", 
            'pos': ", ".join(data['pos']),
            'kalibr': data['kalibr'], 'sht': data['sht'], 'summa': round(data['summa'], 2),
            'norma': norm_val, 'percent': round(percent, 1), 'shift': data['shift']
        })
    rows.sort(key=lambda x: x['percent'])
    return render_template('tabel.html', summary=rows)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)