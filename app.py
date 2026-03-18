import os
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "dilmurat_group_system_2026"
basedir = os.path.abspath(os.path.dirname(__file__))

# === КОНФИГУРАЦИЯ БАЗЫ ДАННЫХ ===
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Исправляем протокол для SQLAlchemy 1.4+
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Добавляем правильный sslmode=require для Render
    if "?sslmode" not in database_url:
        database_url += "?sslmode=require"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    # КОНФИГУРАЦИЯ С ПРАВИЛЬНЫМ SSL
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "connect_args": {
            "sslmode": "require"
        },
        "pool_pre_ping": True,
        "pool_recycle": 300,
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
    otdel = db.Column(db.String(100))  # Добавляем поле otdel

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.String(20))
    date = db.Column(db.String(20))
    otdel = db.Column(db.String(100))
    total_kpd = db.Column(db.Float)
    kalibr = db.Column(db.Float)
    sht = db.Column(db.Float)
    shift = db.Column(db.String(20))
    # Добавляем поле для сохранения коэффициента сложности
    complexity_coefficient = db.Column(db.Float, default=1.0)

# === ФУНКЦИИ РАСЧЕТА СЛОЖНОСТИ ===
def get_complexity_coefficient(kalibr):
    """
    Возвращает коэффициент сложности на основе калибра (веса бабины)
    
    Args:
        kalibr (float): вес бабины в кг
        
    Returns:
        float: коэффициент сложности
    """
    if kalibr is None or kalibr <= 0:
        return 1.0
    
    if kalibr <= 10:
        return 1.5  # очень высокая сложность
    elif kalibr <= 20:
        return 1.3  # высокая сложность
    elif kalibr <= 35:
        return 1.15  # средняя сложность
    else:
        return 1.0  # базовая сложность

def get_category_norm(category):
    """
    Возвращает среднюю норму для категории
    
    Args:
        category (str): категория сотрудника
        
    Returns:
        float: средняя норма в кг
    """
    category_norms = {
        "1": (300 + 450) / 2,  # 375 кг
        "2": (280 + 400) / 2,  # 340 кг
        "3": (250 + 350) / 2,  # 300 кг
        "4": (220 + 280) / 2,  # 250 кг
        "5": (100 + 180) / 2,  # 140 кг
    }
    return category_norms.get(category, 140)  # по умолчанию как 5 категория

def calculate_efficiency_percentage(real_weight, complexity_coeff, category_norm):
    """
    Рассчитывает процент выполнения плана с учетом сложности
    
    Args:
        real_weight (float): реальный вес в кг
        complexity_coeff (float): коэффициент сложности
        category_norm (float): средняя норма категории
        
    Returns:
        float: процент выполнения плана
    """
    if category_norm <= 0:
        return 0
    
    effective_weight = real_weight * complexity_coeff
    percentage = (effective_weight / category_norm) * 100
    return round(percentage, 1)

# === ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ===
# Создаем таблицы и добавляем недостающие поля для локальной базы
if not database_url:
    with app.app_context():
        db.create_all()
        
        # Проверяем и добавляем поле complexity_coefficient если его нет
        try:
            from sqlalchemy import text
            
            # Проверяем и добавляем поле complexity_coefficient в record
            result = db.session.execute(text("PRAGMA table_info(record)"))
            columns = [row[1] for row in result]
            
            if 'complexity_coefficient' not in columns:
                print("Добавляю поле complexity_coefficient в таблицу record...")
                db.session.execute(text("ALTER TABLE record ADD COLUMN complexity_coefficient REAL DEFAULT 1.0"))
                db.session.commit()
                print("Поле complexity_coefficient успешно добавлено")
            else:
                print("Поле complexity_coefficient уже существует")
                
            # Проверяем и добавляем поле otdel в worker
            result = db.session.execute(text("PRAGMA table_info(worker)"))
            columns = [row[1] for row in result]
            
            if 'otdel' not in columns:
                print("Добавляю поле otdel в таблицу worker...")
                db.session.execute(text("ALTER TABLE worker ADD COLUMN otdel VARCHAR(100) DEFAULT 'Qiyma'"))
                db.session.commit()
                print("Поле otdel успешно добавлено")
            else:
                print("Поле otdel уже существует")
                
        except Exception as e:
            print(f"Ошибка при добавлении полей: {e}")
            db.session.rollback()

# === МАРШРУТЫ ===

# Добавляем логирование
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # Безопасная инициализация базы при первом запросе
        if database_url:
            try:
                db.create_all()
                # Проверяем есть ли работники
                workers_count = Worker.query.count()
                if workers_count == 0:
                    workers = [
                        Worker(worker_id='5', fio='Дилмурат Бобомуродов', category='5', otdel='Qiyma'),
                        Worker(worker_id='7', fio='Сотрудник 7', category='5', otdel='Qiyma'),
                        Worker(worker_id='8', fio='Сотрудник 8', category='4', otdel='Kesib'),
                        Worker(worker_id='9', fio='Сотрудник 9', category='3', otdel='Kesib'),
                    ]
                    for worker in workers:
                        db.session.add(worker)
                    db.session.commit()
                    logger.info("Добавлены базовые работники для Render")
            except Exception as e:
                logger.error(f"Ошибка инициализации базы: {e}")
                return f"Ошибка подключения к базе: {e}", 500
        else:
            # Локальная база
            db.create_all()
        
        if request.method == 'POST':
            data = request.form.get('bulk_workers', '')
            for line in data.strip().split('\n'):
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    wid = parts[0].strip()
                    # Если такой ID уже есть, обновляем имя и категорию, а не выдаем ошибку
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
    worker = Worker.query.get(id)
    if worker:
        db.session.delete(worker)
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
                    # Получаем калибр и рассчитываем коэффициент сложности
                    kalibr = float(p[3].replace(',', '.'))
                    complexity_coeff = get_complexity_coefficient(kalibr)
                    
                    db.session.add(Record(
                        worker_id=wid, date=date_str, otdel=p[1],
                        total_kpd=float(p[2].replace(',', '.')), 
                        kalibr=kalibr, 
                        sht=float(p[4].replace(',', '.')), 
                        shift=p[5] if len(p) > 5 else "Ночь",
                        complexity_coefficient=complexity_coeff  # сохраняем коэффициент
                    ))
                except: continue
    db.session.commit()
    return redirect(url_for('tabel'))

@app.route('/tabel')
def tabel():
    try:
        logger.info("Страница табеля загружается")
        
        # Получаем значения из полей поиска
        search_date = request.args.get('search_date', '')
        search_id = request.args.get('search_id', '')

        records = Record.query.all()
        logger.info(f"Найдено записей: {len(records)}")
        
        norms = {"1": 300, "2": 280, "3": 250, "4": 220, "5": 100}
        grouped = {}

        for r in records:
            key = (r.date, r.shift, r.worker_id)
            if key not in grouped:
                grouped[key] = {
                    'id_db': r.id, 'date': r.date, 'id': r.worker_id, 'pos': [r.otdel],
                    'kalibr': r.kalibr, 'sht': r.sht, 'summa': r.total_kpd, 'shift': r.shift
                }
            else:
                if r.otdel not in grouped[key]['pos']:
                    grouped[key]['pos'].append(r.otdel)
                grouped[key]['summa'] += r.total_kpd
                grouped[key]['sht'] += r.sht
        
        rows = []
        for data in grouped.values():
            # --- ЛОГИКА ФИЛЬТРАЦИИ ---
            # Если в поиске что-то есть, и оно не совпадает с данными — пропускаем эту строку
            if search_date and search_date != data['date']:
                continue
            if search_id and search_id != data['id']:
                continue
            # ------------------------

            w = Worker.query.filter_by(worker_id=data['id']).first()
            if not w:
                logger.warning(f"Не найден работник с ID: {data['id']}")
                continue
            
            # Получаем категорию и норму
            category = w.category if w else "5"
            category_norm = get_category_norm(category)
            
            # Рассчитываем коэффициент сложности на основе калибра
            complexity_coeff = get_complexity_coefficient(data['kalibr'])
            
            # Рассчитываем процент выполнения с учетом сложности
            real_weight = data['summa']
            effective_weight = real_weight * complexity_coeff
            percentage = calculate_efficiency_percentage(real_weight, complexity_coeff, category_norm)
            
            rows.append({
                'db_id': data['id_db'],
                'date': data['date'],
                'id': data['id'],
                'fio': w.fio if w else "-",
                'cat': category, 
                'pos': ", ".join(data['pos']),
                'kalibr': data['kalibr'], 
                'sht': data['sht'], 
                'summa': round(real_weight, 2),           # реальный вес
                'effective_weight': round(effective_weight, 2),  # эффективный вес
                'complexity_coeff': complexity_coeff,           # коэффициент сложности
                'norma': category_norm, 
                'percent': percentage, 
                'shift': data['shift']
            })

        # Сортировка: сначала те, у кого КПД < 80, затем по дате/смене
        rows.sort(key=lambda x: (x['percent'] >= 80, x['date'], x['shift']), reverse=False)
        
        # Подсчет тоннажа по сменам
        total_day_kg = sum(row['summa'] for row in rows if row['shift'] == 'День')
        total_night_kg = sum(row['summa'] for row in rows if row['shift'] == 'Ночь')
        total_day_tons = round(total_day_kg / 1000, 2)
        total_night_tons = round(total_night_kg / 1000, 2)

        logger.info(f"Подготовлено строк для таблицы: {len(rows)}")
        return render_template('tabel.html', summary=rows, search_date=search_date, search_id=search_id,
                             total_day_tons=total_day_tons, total_night_tons=total_night_tons)
    except Exception as e:
        logger.error(f"Ошибка страницы табеля: {e}")
        return f"Ошибка: {e}", 500

@app.route('/delete_record/<int:id>', methods=['POST'])
def delete_record(id):
    try:
        rec = Record.query.get(id)
        if rec:
            Record.query.filter_by(worker_id=rec.worker_id, date=rec.date, shift=rec.shift).delete()
            db.session.commit()
        
        # Получаем текущие параметры для перенаправления
        search_date = request.form.get('search_date', request.args.get('search_date', ''))
        search_id = request.form.get('search_id', request.args.get('search_id', ''))
        
        # Формируем URL с сохранением параметров
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
        
        # Получаем ID записей для удаления
        data = request.get_json()
        if not data or 'ids' not in data:
            return {'success': False, 'error': 'Не указаны ID записей'}
        
        ids = data['ids']
        if not isinstance(ids, list) or not ids:
            return {'success': False, 'error': 'Некорректный формат ID'}
        
        # Удаляем записи
        deleted_count = 0
        for record_id in ids:
            try:
                rec = Record.query.get(record_id)
                if rec:
                    Record.query.filter_by(worker_id=rec.worker_id, date=rec.date, shift=rec.shift).delete()
                    deleted_count += 1
            except:
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
