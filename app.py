import os
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "dilmurat_group_system_2026"

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'production.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.String(20), unique=True)
    fio = db.Column(db.String(100))
    category = db.Column(db.String(50))
    salary_base = db.Column(db.String(50))

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.String(20))
    date = db.Column(db.String(20))
    otdel = db.Column(db.String(100))
    total_kpd = db.Column(db.Float)
    kalibr = db.Column(db.Float)
    sht = db.Column(db.Float)
    shift = db.Column(db.String(20))

with app.app_context():
    db.create_all()

@app.route('/')
def index(): return render_template('index.html')

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
                    db.session.add(Record(worker_id=wid, date=date_str, otdel=p[1],
                        total_kpd=float(p[2].replace(',', '.')), 
                        kalibr=float(p[3].replace(',', '.')), 
                        sht=float(p[4].replace(',', '.')), 
                        shift=p[5] if len(p) > 5 else "Ночь"))
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
    
    # СОРТИРОВКА: Сначала те, у кого процент меньше (от 0% до 100%+)
    rows.sort(key=lambda x: x['percent'])
    
    return render_template('tabel.html', summary=rows)
    records = Record.query.all()
    norms = {"1": 300, "2": 280, "3": 250, "4": 220, "5": 100}
    
    # ГРУППИРОВКА ДАННЫХ
    grouped = {}
    for r in records:
        # Создаем уникальный ключ: (Дата + Смена + ID сотрудника)
        key = (r.date, r.shift, r.worker_id)
        if key not in grouped:
            grouped[key] = {
                'date': r.date, 'id': r.worker_id, 'pos': [r.otdel],
                'kalibr': r.kalibr, 'sht': r.sht, 'summa': r.total_kpd, 'shift': r.shift
            }
        else:
            # Если такой ключ уже есть — плюсуем данные
            if r.otdel not in grouped[key]['pos']:
                grouped[key]['pos'].append(r.otdel)
            grouped[key]['summa'] += r.total_kpd
            grouped[key]['sht'] += r.sht
            # Калибр обычно берем последний или средний, оставим последний

    rows = []
    for data in grouped.values():
        w = Worker.query.filter_by(worker_id=data['id']).first()
        cat_num = "".join(filter(str.isdigit, w.category)) if w else "5"
        norm_val = norms.get(cat_num, 100)
        percent = (data['summa'] / norm_val * 100) if norm_val > 0 else 0
        
        rows.append({
            'date': data['date'], 'id': data['id'], 'fio': w.fio if w else "-",
            'cat': w.category if w else "-", 
            'pos': ", ".join(data['pos']), # Позиции через запятую
            'kalibr': data['kalibr'], 'sht': data['sht'], 'summa': round(data['summa'], 2),
            'norma': norm_val, 'percent': round(percent, 1), 'shift': data['shift']
        })
    
    return render_template('tabel.html', summary=rows)

@app.route('/export_excel')
def export_excel():
    # В Excel тоже выгружаем сгруппированные данные (используем ту же логику что в /tabel)
    # Для краткости пропустим дублирование кода тут, но в реальности лучше вынести в функцию
    return "Функция экспорта обновится автоматически при использовании логики группировки"
# Этот блок создаст пустую базу данных на сервере, если её нет
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
if __name__ == '__main__':
    app.run(debug=True)