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
    # Внутренний URL базы Render с правильным диалектом postgresql
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bank_db_1wkx_user:YFfVKou0OojY6x2Kf2KQDH6XFphP7h0h@dpg-d61fa9fpm1nc73879e70-a/bank_db_1wkx?sslmode=require'
    
    # Параметры движка (обязательно)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
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
    __tablename__ = 'record'
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
        # Проверяем существующие таблицы
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Существующие таблицы: {existing_tables}")
        
        # Создаем таблицы
        db.create_all()
        logger.info("Таблицы созданы или уже существуют")
        
        # Проверяем таблицы после создания
        inspector = db.inspect(db.engine)
        tables_after = inspector.get_table_names()
        logger.info(f"Таблицы после создания: {tables_after}")
        
        # Проверяем соединение с базой
        try:
            from sqlalchemy import text
            db.engine.execute(text("SELECT 1"))
            logger.info("Соединение с базой данных работает")
        except Exception as conn_error:
            logger.error(f"Ошибка соединения с базой: {conn_error}")
        
    except Exception as e:
        logger.error(f"Ошибка создания таблиц: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        pass

    # Добавляем начальных работников
    if database_url:
        try:
            workers_count = Worker.query.count()
            logger.info(f"Текущее количество работников: {workers_count}")
            if workers_count == 0:
                logger.info("Добавляем начальных работников")
                workers = [
                    Worker(worker_id='5', fio='Дилмурат Бобомуродов', category='5', otdel='Qiyma'),
                    Worker(worker_id='7', fio='Сотрудник 7', category='5', otdel='Qiyma'),
                    Worker(worker_id='8', fio='Сотрудник 8', category='4', otdel='Kesib'),
                    Worker(worker_id='9', fio='Сотрудник 9', category='3', otdel='Kesib'),
                ]
                for worker in workers:
                    db.session.add(worker)
                db.session.commit()
                logger.info("Работники добавлены")
                
                # Проверяем после добавления
                workers_after = Worker.query.all()
                logger.info(f"Работники после добавления: {len(workers_after)}")
                for w in workers_after:
                    logger.info(f"  - {w.worker_id}: {w.fio}")
        except Exception as e:
            logger.error(f"Ошибка добавления работников: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            db.session.rollback()
    else:
        logger.info("Работаем с локальной базой SQLite")

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
            logger.info(f"Получены данные для добавления работников: {repr(data[:100])}")
            
            if data.strip():
                lines = data.strip().split('\n')
                logger.info(f"Количество строк для обработки: {len(lines)}")
                
                for i, line in enumerate(lines):
                    parts = line.strip().split('\t')
                    logger.info(f"Строка {i+1}: {repr(line)}, частей: {len(parts)}")
                    
                    if len(parts) >= 2:
                        worker_id = parts[0].strip()
                        fio = parts[1].strip()
                        category = parts[2].strip() if len(parts) > 2 else "5"
                        otdel = parts[3].strip() if len(parts) > 3 else "Qiyma"
                        
                        logger.info(f"Обработка работника: ID={worker_id}, ФИО={fio}, Категория={category}, Отдел={otdel}")
                        
                        try:
                            existing = Worker.query.filter_by(worker_id=worker_id).first()
                            if existing:
                                existing.fio = fio
                                existing.category = category
                                existing.otdel = otdel
                                logger.info(f"Обновлен работник: {worker_id}")
                            else:
                                new_worker = Worker(
                                    worker_id=worker_id,
                                    fio=fio,
                                    category=category,
                                    otdel=otdel
                                )
                                db.session.add(new_worker)
                                logger.info(f"Добавлен новый работник: {worker_id}")
                        except Exception as worker_error:
                            logger.error(f"Ошибка сохранения работника {worker_id}: {worker_error}")
                            continue
                
                try:
                    db.session.commit()
                    logger.info("Изменения в сотрудниках сохранены в базу")
                except Exception as commit_error:
                    logger.error(f"Ошибка коммита: {commit_error}")
                    db.session.rollback()
            else:
                logger.info("Пустые данные для добавления работников")
            
            return redirect(url_for('workers'))
        
        # GET запрос - отображаем всех сотрудников
        try:
            all_workers = Worker.query.order_by(Worker.worker_id.asc()).all()
            logger.info(f"Найдено работников в базе: {len(all_workers)}")
            for worker in all_workers:
                logger.info(f"Работник: {worker.worker_id} - {worker.fio}")
            return render_template('workers.html', workers=all_workers)
        except Exception as db_error:
            logger.error(f"Ошибка получения работников: {db_error}")
            return render_template('workers.html', workers=[], error="База временно недоступена")
    except Exception as e:
        logger.error(f"Ошибка в маршруте workers: {e}")
        return f"Ошибка сервера: {str(e)}", 500

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
        logger.info(f"Получены данные для bulk_input: дата={date_str}, данные={repr(data[:100])}")
        
        if data.strip():
            lines = data.strip().split('\n')
            logger.info(f"Количество строк для обработки: {len(lines)}")
            
            for i, line in enumerate(lines):
                p = line.split()
                logger.info(f"Строка {i+1}: {repr(line)}, элементов: {len(p)}")
                
                if len(p) >= 5:
                    wid = p[0].strip()
                    logger.info(f"Обработка записи для работника: {wid}")
                    
                    # Проверяем, существует ли работник
                    worker = Worker.query.filter_by(worker_id=wid).first()
                    if worker:
                        logger.info(f"Работник {wid} найден: {worker.fio}")
                        try:
                            kalibr = float(p[3].replace(',', '.'))
                            complexity_coeff = get_complexity_coefficient(kalibr)
                            
                            # Создаем запись напрямую через SQLAlchemy
                            new_record = Record(
                                worker_id=wid,
                                date=date_str,
                                otdel=p[1],
                                total_kpd=float(p[2].replace(',', '.')),
                                kalibr=kalibr,
                                sht=float(p[4].replace(',', '.')),
                                shift=p[5] if len(p) > 5 else "Ночь",
                                complexity_coefficient=complexity_coeff
                            )
                            db.session.add(new_record)
                            logger.info(f"Добавлена запись для работника {wid} за {date_str}")
                        except Exception as record_error:
                            logger.error(f"Ошибка добавления записи для {wid}: {record_error}")
                            continue
                    else:
                        logger.warning(f"Работник {wid} не найден, запись пропущена")
                else:
                    logger.warning(f"Строка {i+1} имеет недостаточно элементов: {len(p)}")
            
            try:
                db.session.commit()
                logger.info("Все записи успешно сохранены в базу")
            except Exception as commit_error:
                logger.error(f"Ошибка коммита записей: {commit_error}")
                db.session.rollback()
        else:
            logger.info("Пустые данные для bulk_input")
        
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
            # Получаем записи напрямую из базы
            records = Record.query.all()
        except Exception as db_error:
            logger.error(f"Ошибка доступа к базе: {db_error}")
            records = []
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
        record = Record.query.get(id)
        if record:
            db.session.delete(record)
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
        
        try:
            db.session.commit()
            logger.info(f"Удалено {deleted_count} записей")
        except Exception as commit_error:
            logger.error(f"Ошибка коммита при массовом удалении: {commit_error}")
            db.session.rollback()
            return {'success': False, 'error': 'Ошибка сохранения изменений'}
        
        return {'success': True, 'deleted_count': deleted_count}
    except Exception as e:
        logger.error(f"Ошибка массового удаления: {e}")
        return {'success': False, 'error': str(e)}

@app.route('/test_db')
def test_db():
    try:
        # Проверяем работников
        workers = Worker.query.all()
        worker_info = []
        for w in workers:
            worker_info.append(f"{w.worker_id}: {w.fio} ({w.category}, {w.otdel})")
        
        # Проверяем записи
        records = Record.query.all()
        record_info = []
        for r in records:
            record_info.append(f"{r.date}: {r.worker_id} - {r.total_kpd}kg")
        
        return f"""
        <h2>Проверка базы данных</h2>
        <h3>Работники ({len(workers)}):</h3>
        <pre>{chr(10).join(worker_info)}</pre>
        <h3>Записи ({len(records)}):</h3>
        <pre>{chr(10).join(record_info)}</pre>
        <a href="/">Назад</a>
        """
    except Exception as e:
        return f"Ошибка: {str(e)}"

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
