from flask import current_app

def add_record(app, record):
    """Добавление новой записи"""
    with app.app_context():
        db = current_app.extensions['sqlalchemy'].db
        
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
        
        new_rec = Record(**record)
        db.session.add(new_rec)
        db.session.commit()
        return new_rec

def get_all_records(app):
    """Получение всех записей"""
    with app.app_context():
        db = current_app.extensions['sqlalchemy'].db
        
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
        
        return Record.query.all()

def update_record(app, id, data):
    """Обновление записи"""
    with app.app_context():
        db = current_app.extensions['sqlalchemy'].db
        
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
        
        record = Record.query.get(id)
        if record:
            for key, value in data.items():
                setattr(record, key, value)
            db.session.commit()
        return record

def get_records_by_date(app, date):
    """Получение записей по дате"""
    with app.app_context():
        db = current_app.extensions['sqlalchemy'].db
        
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
        
        return Record.query.filter_by(date=date).all()

def get_record_by_id(app, id):
    """Получение записи по ID"""
    with app.app_context():
        db = current_app.extensions['sqlalchemy'].db
        
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
        
        return Record.query.get(id)

def delete_record(app, id):
    """Удаление записи"""
    with app.app_context():
        db = current_app.extensions['sqlalchemy'].db
        
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
        
        record = Record.query.get(id)
        if record:
            db.session.delete(record)
            db.session.commit()
            return True
        return False
