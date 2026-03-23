import os
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file, current_app
from flask_sqlalchemy import SQLAlchemy

# Добавляем логирование
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "dilmurat_group_system_2026"
basedir = os.path.abspath(os.path.dirname(__file__))

# === КОНФИГУРАЦИЯ БАЗЫ ДАННЫХ ===
database_url = os.getenv('DATABASE_URL')

if database_url:
    # Внешний URL базы Render (самый стабильный вариант)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://bank_db_1wkx_user:YFfVKou0OojY6x2Kf2KQDH6XFphP7h0h@dpg-d61fa9fpm1nc73879e70-a.oregon-postgres.render.com:5432/bank_db_1wkx?sslmode=require'
    
    # Параметры движка для SSL
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'connect_args': {'sslmode': 'require'}
    }
else:
    # Локальная база (SQLite) - используем production.db где хранятся данные
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'production.db')

db = SQLAlchemy(app)

# === МОДЕЛИ ===
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.String(20), unique=True)
    fio = db.Column(db.String(100))
    category = db.Column(db.String(50))
    otdel = db.Column(db.String(100))

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.String(20))
    date = db.Column(db.String(20))
    otdel = db.Column(db.String(100))
    total_kpd = db.Column(db.Float)
    kalibr = db.Column(db.Float)
    sht = db.Column(db.Float)
    shift = db.Column(db.String(20))
    complexity_coefficient = db.Column(db.Float, default=1.0)

# === ФУНКЦИИ РАСЧЕТА ===
def get_complexity_coefficient(kalibr):
    if kalibr is None or kalibr <= 0:
        return 1.0
    if kalibr <= 10:
        return 1.5
    elif kalibr <= 20:
        return 1.3
    elif kalibr <= 35:
        return 1.15
    else:
        return 1.0

def get_category_norm(category, kalibr=None, otdel=None):
    if otdel != "Turk":
        category_norms = {
            "1": (300 + 450) / 2,
            "2": (280 + 400) / 2,
            "3": (250 + 350) / 2,
            "4": (220 + 280) / 2,
            "5": (100 + 180) / 2,
        }
        return category_norms.get(category, 140)
    
    if kalibr is None:
        kalibr = 30
    
    standard_kalibrs = [20, 30, 40]
    nearest_kalibr = min(standard_kalibrs, key=lambda x: abs(x - kalibr))
    
    plans_pieces = {
        "1": {20: 15, 30: 12, 40: 10},
        "2": {20: 13, 30: 10, 40: 9},
        "3": {20: 11, 30: 8, 40: 7},
        "4": {20: 9, 30: 7, 40: 6},
        "5": {20: 8, 30: 6, 40: 5},
    }
    
    pieces = plans_pieces.get(category, {20: 8, 30: 6, 40: 5}).get(nearest_kalibr, 6)
    norm_kg = pieces * kalibr
    return norm_kg

def get_pieces_plan(category, kalibr, otdel):
    if otdel != "Turk":
        return None
    if kalibr is None:
        kalibr = 30
    standard_kalibrs = [20, 30, 40]
    nearest_kalibr = min(standard_kalibrs, key=lambda x: abs(x - kalibr))
    plans_pieces = {
        "1": {20: 15, 30: 12, 40: 10},
        "2": {20: 13, 30: 10, 40: 9},
        "3": {20: 11, 30: 8, 40: 7},
        "4": {20: 9, 30: 7, 40: 6},
        "5": {20: 8, 30: 6, 40: 5},
    }
    return plans_pieces.get(category, {20: 8, 30: 6, 40: 5}).get(nearest_kalibr, 6)

def calculate_efficiency_percentage(real_weight, complexity_coeff, category_norm):
    if category_norm <= 0:
        return 0
    effective_weight = real_weight * complexity_coeff
    percentage = (effective_weight / category_norm) * 100
    return round(percentage, 1)

# === СОЗДАНИЕ ТАБЛИЦ ===
with app.app_context():
    try:
        db.create_all()
        logger.info("Таблицы созданы или уже существуют")
    except Exception as e:
        logger.error(f"Ошибка создания таблиц: {str(e)}")
        # Если база недоступна — не падаем полностью
        pass

    # Добавляем начальных работников ТОЛЬКО если таблица пустая
    if database_url:
        try:
            workers_count = Worker.query.count()
            if workers_count == 0:
                logger.info("Добавляем начальных работников")
                workers = [
                    Worker(worker_id='5', fio='Дилмурат Бобомуродов', category='5', otdel='Qiyma'),
                    Worker(worker_id='7', fio='Сотрудник 7', category='5', otdel='Qiyma'),
                    Worker(worker_id='8', fio='Сотрудник 8', category='4', otdel='Kesib'),
                    Worker(worker_id='9', fio='Сотрудник 9', category='3', otdel='Kesib'),
                ]
                db.session.bulk_save_objects(workers)
                db.session.commit()
                logger.info("Работники добавлены")
        except Exception as e:
            logger.error(f"Ошибка добавления работников: {str(e)}")
            db.session.rollback()

# === МАРШРУТЫ ===
@app.route('/')
def index():
    try:
        logger.info("Главная страница загружается")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Ошибка главной страницы: {e}")
        return f"Ошибка: {e}", 500

@app.route('/workers', methods=['GET', 'POST'])
def workers():
    try:
        if request.method == 'POST':
            data = request.form.get('bulk_workers', '')
            for line in data.strip().split('\n'):
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    wid = parts[0].strip()
                    existing = Worker.query.filter_by(worker_id=wid).first()
                    if existing:
                        existing.fio = parts[1].strip()
                        existing.category = parts[2].strip() if len(parts) > 2 else existing.category
                        existing.otdel = parts[3].strip() if len(parts) > 3 else existing.otdel
                    else:
                        db.session.add(Worker(
                            worker_id=wid,
                            fio=parts[1].strip(),
                            category=parts[2].strip() if len(parts) > 2 else "5",
                            otdel=parts[3].strip() if len(parts) > 3 else "Qiyma"
                        ))
            db.session.commit()
            return redirect(url_for('workers'))
        
        all_workers = Worker.query.order_by(Worker.worker_id.asc()).all()
        return render_template('workers.html', workers=all_workers)
    except Exception as e:
        logger.error(f"Ошибка в маршруте workers: {e}")
        return f"Ошибка: {e}", 500

@app.route('/delete_worker/<int:id>')
def delete_worker(id):
    try:
        worker = Worker.query.get(id)
        if worker:
            db.session.delete(worker)
            db.session.commit()
    except Exception as e:
        logger.error(f"Ошибка удаления работника: {e}")
    return redirect(url_for('workers'))

@app.route('/bulk_input', methods=['POST'])
def bulk_input():
    try:
        data = request.form.get('bulk_data', '')
        date_str = request.form.get('date', '')
        for line in data.strip().split('\n'):
            p = line.split()
            if len(p) >= 5:
                wid = p[0].strip()
                if Worker.query.filter_by(worker_id=wid).first():
                    try:
                        kalibr = float(p[3].replace(',', '.'))
                        complexity_coeff = get_complexity_coefficient(kalibr)
                        db.session.add(Record(
                            worker_id=wid, date=date_str, otdel=p[1],
                            total_kpd=float(p[2].replace(',', '.')), 
                            kalibr=kalibr, 
                            sht=float(p[4].replace(',', '.')), 
                            shift=p[5] if len(p) > 5 else "Ночь",
                            complexity_coefficient=complexity_coeff
                        ))
                    except:
                        continue
        db.session.commit()
    except Exception as e:
        logger.error(f"Ошибка массового ввода: {e}")
    return redirect(url_for('tabel'))

@app.route('/tabel')
def tabel():
    try:
        logger.info("Страница табеля загружается")
        
        search_date = request.args.get('search_date', '')
        search_id = request.args.get('search_id', '')

        try:
            records = Record.query.all()
        except Exception as db_error:
            logger.error(f"Ошибка доступа к базе: {db_error}")
            records = []
            # Возвращаем страницу с сообщением об ошибке
            return render_template('tabel.html', summary=[], error="База временно недоступена", 
                               search_date=search_date, search_id=search_id,
                               total_day_tons=0, total_night_tons=0)
        
        logger.info(f"Найдено записей: {len(records)}")
        
        if not records:
            return render_template('tabel.html', summary=[], search_date=search_date, search_id=search_id,
                               total_day_tons=0, total_night_tons=0)
        
        grouped = {}

        for r in records:
            key = (r.date, r.shift, r.worker_id)
            raw_otdel = r.otdel
            if isinstance(raw_otdel, list):
                current_pos = raw_otdel
            else:
                clean_str = str(raw_otdel).replace('[', '').replace(']', '').replace("'", "").replace('"', '')
                current_pos = [p.strip() for p in clean_str.split(',') if p.strip()]

            if key not in grouped:
                grouped[key] = {
                    'id_db': r.id,
                    'date': r.date, 
                    'id': r.worker_id, 
                    'pos': current_pos,
                    'kalibr': r.kalibr or 30, 
                    'sht': r.sht or 0, 
                    'summa': r.total_kpd or 0, 
                    'shift': r.shift
                }
            else:
                for p in current_pos:
                    if p not in grouped[key]['pos']:
                        grouped[key]['pos'].append(p)
                grouped[key]['summa'] += (r.total_kpd or 0)
                grouped[key]['sht'] += (r.sht or 0)
        
        rows = []
        for data in grouped.values():
            if search_date and search_date != data['date']:
                continue
            if search_id and search_id != data['id']:
                continue

            try:
                w = Worker.query.filter_by(worker_id=data['id']).first()
                if not w:
                    continue
                
                category = w.category if w else "5"
                otdel = data['pos'][0] if data['pos'] and len(data['pos']) > 0 else "Qiyma"
                category_norm = get_category_norm(category, data['kalibr'], otdel)
                complexity_coeff = get_complexity_coefficient(data['kalibr'])
                real_weight = data['summa']
                effective_weight = real_weight * complexity_coeff
                percentage = calculate_efficiency_percentage(real_weight, complexity_coeff, category_norm)
                pieces_plan = get_pieces_plan(category, data['kalibr'], otdel)
                
                rows.append({
                    'db_id': data['id_db'],
                    'date': data['date'],
                    'id': data['id'],
                    'fio': w.fio if w else "-",
                    'cat': category, 
                    'pos': ", ".join(data['pos']) if isinstance(data['pos'], list) else str(data['pos']),
                    'kalibr': data['kalibr'], 
                    'sht': data['sht'], 
                    'summa': round(real_weight, 2),
                    'effective_weight': round(effective_weight, 2),
                    'complexity_coeff': complexity_coeff,
                    'norma': category_norm, 
                    'pieces_plan': pieces_plan,
                    'percent': percentage, 
                    'shift': data['shift']
                })
            except Exception as row_error:
                logger.error(f"Ошибка обработки строки: {row_error}")
                continue

        rows.sort(key=lambda x: (x['percent'] >= 80, x['date'], x['shift']), reverse=False)
        
        total_day_kg = sum(row['summa'] for row in rows if row['shift'] == 'День')
        total_night_kg = sum(row['summa'] for row in rows if row['shift'] == 'Ночь')
        total_day_tons = round(total_day_kg / 1000, 2)
        total_night_tons = round(total_night_kg / 1000, 2)

        logger.info(f"Подготовлено строк для таблицы: {len(rows)}")
        return render_template('tabel.html', summary=rows, search_date=search_date, search_id=search_id,
                             total_day_tons=total_day_tons, total_night_tons=total_night_tons)
    except Exception as e:
        logger.error(f"Критическая ошибка в /tabel: {e}")
        return f"Ошибка сервера: {str(e)}", 500

@app.route('/delete_record/<int:id>', methods=['POST'])
def delete_record(id):
    try:
        rec = Record.query.get(id)
        if rec:
            db.session.delete(rec)
            db.session.commit()
            logger.info(f"Удалена запись с ID: {id}")
        
        search_date = request.form.get('search_date', request.args.get('search_date', ''))
        search_id = request.form.get('search_id', request.args.get('search_id', ''))
        
        params = []
        if search_date:
            params.append(f"search_date={search_date}")
        if search_id:
            params.append(f"search_id={search_id}")
        
        redirect_url = "/tabel"
        if params:
            redirect_url += "?" + "&".join(params)
        
        return redirect(redirect_url)
    except Exception as e:
        logger.error(f"Ошибка удаления записи: {e}")
        return redirect("/tabel")

@app.route('/delete_multiple', methods=['POST'])
def delete_multiple():
    try:
        from flask import request
        
        data = request.get_json()
        if not data or 'ids' not in data:
            return {'success': False, 'error': 'Не указаны ID записей'}
        
        ids = data['ids']
        if not isinstance(ids, list) or not ids:
            return {'success': False, 'error': 'Некорректный формат ID'}
        
        deleted_count = 0
        for record_id in ids:
            try:
                rec = Record.query.get(record_id)
                if rec:
                    db.session.delete(rec)
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Ошибка удаления записи {record_id}: {e}")
                continue
        
        db.session.commit()
        logger.info(f"Удалено {deleted_count} записей")
        
        return {'success': True, 'deleted_count': deleted_count}
    except Exception as e:
        logger.error(f"Ошибка массового удаления: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

@app.route('/export_excel')
def export_excel():
    try:
        records = Record.query.all()
        data_for_excel = []
        for r in records:
            w = Worker.query.filter_by(worker_id=r.worker_id).first()
            data_for_excel.append({
                'Дата': r.date, 'ID': r.worker_id, 'ФИО': w.fio if w else "-",
                'КПД': r.total_kpd, 'Смена': r.shift
            })
        df = pd.DataFrame(data_for_excel).sort_values(by=['Дата', 'ID'])
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name="Report_KPD.xlsx")
    except Exception as e:
        logger.error(f"Ошибка экспорта Excel: {e}")
        return f"Ошибка: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
