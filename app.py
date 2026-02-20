from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import os
from werkzeug.utils import secure_filename
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment
import io
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# Папка для временной загрузки фото
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Список товаров (твои реальные позиции)
PRODUCTS = [
    "DONER 100 QYMA",
    "DONER 30/70",
    "DONER 50/50 BELORUS",
    "DONER 50/50 CITY",
    "DONER 50/50 SEVIMLI",
    "DONER 50/50 YUMA",
    "DONER 60/40 YUMA",
    "DONER 70/30",
    "DONER TOVUQ",
    "Сихлаш",
    "Фарш говяжий"
]

# Реальные работники с ID, категорией и ставками
WORKERS_TABLE = [
    {"id": "1", "fio": "Ахмедов Ахмед", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "2", "fio": "Бобоев Бобо", "category": "сихлаш 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "3", "fio": "Валиев Вали", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "4", "fio": "Ганиев Гани", "category": "сихлаш 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "5", "fio": "Давлатов Давлат", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "6", "fio": "Ерматов Ермат", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "7", "fio": "Жураев Жура", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "8", "fio": "Зокиров Зокир", "category": "сихлаш 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "9", "fio": "Ибрагимов Ибрагим", "category": "сихлаш 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "10", "fio": "Каримов Карим", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "11", "fio": "Латипов Латип", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "12", "fio": "Маматов Мамат", "category": "сихлаш 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "13", "fio": "Норматов Нормат", "category": "сихлаш 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "14", "fio": "Олимов Олим", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "15", "fio": "Пардаев Парда", "category": "сихлаш стаж", "rate_month": 3500000, "daily_rate": 116667, "bonus_percent": 20},
    {"id": "16", "fio": "Рахимов Рахим", "category": "сихлаш 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "17", "fio": "Саидов Саид", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "18", "fio": "Тошматов Тошмат", "category": "сихлаш 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "19", "fio": "Умаров Умар", "category": "сихлаш 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "20", "fio": "Фазлиев Фазли", "category": "сихлаш 1 кат", "rate_month": 6440000, "daily_rate": 214667, "bonus_percent": 20},
    {"id": "21", "fio": "Хакимов Хаким", "category": "сихлаш 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "22", "fio": "Чориев Чори", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "23", "fio": "Шарипов Шарип", "category": "сихлаш 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "24", "fio": "Эшматов Эшмат", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "25", "fio": "Юлдашев Юлдаш", "category": "сихлаш 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "26", "fio": "Якубов Якуб", "category": "сихлаш 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "27", "fio": "Абдуллаев Абдулла", "category": "сихлаш 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "28", "fio": "Бахтиёров Бахтиёр", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "29", "fio": "Вохидов Вохид", "category": "сихлаш 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "30", "fio": "Гуломов Гулом", "category": "сихлаш 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "31", "fio": "Дилшодова Дилшод", "category": "сихлаш 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "32", "fio": "Ермакова Елена", "category": "сихлаш 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "33", "fio": "Жасминова Жасмин", "category": "сихлаш 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "34", "fio": "Зарифова Зарифа", "category": "сихлаш 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "35", "fio": "Иродова Ирода", "category": "сихлаш 1 кат", "rate_month": 6440000, "daily_rate": 214667, "bonus_percent": 20},
    {"id": "36", "fio": "Камолова Камола", "category": "сихлаш 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "37", "fio": "Лолова Лола", "category": "сихлаш 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "38", "fio": "Маликова Малика", "category": "сихлаш 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "39", "fio": "Наргизова Наргиза", "category": "сихлаш 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "40", "fio": "Озодова Озода", "category": "сихлаш 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "41", "fio": "Парвинова Парвин", "category": "сихлаш стаж", "rate_month": 3500000, "daily_rate": 116667, "bonus_percent": 20},
    # Разделка
    {"id": "42", "fio": "Ранова Рано", "category": "разделка 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "43", "fio": "Саодатова Саодат", "category": "разделка 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "44", "fio": "Танзилова Танзила", "category": "разделка 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "45", "fio": "Умидова Умида", "category": "разделка 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "46", "fio": "Фаридова Фарида", "category": "разделка 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "47", "fio": "Хадичова Хадича", "category": "разделка 1 кат", "rate_month": 6440000, "daily_rate": 214667, "bonus_percent": 20},
    {"id": "48", "fio": "Чаросова Чарос", "category": "разделка 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "49", "fio": "Шохидова Шохида", "category": "разделка 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "50", "fio": "Элмирова Элмира", "category": "разделка 1 кат", "rate_month": 6440000, "daily_rate": 214667, "bonus_percent": 20},
    {"id": "51", "fio": "Юлдузова Юлдуз", "category": "разделка 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "52", "fio": "Замирова Замира", "category": "разделка 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "53", "fio": "Азаматов Азамат", "category": "разделка 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "54", "fio": "Бехзодов Бехзод", "category": "разделка 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "55", "fio": "Викторов Виктор", "category": "разделка 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "56", "fio": "Георгиев Георгий", "category": "разделка 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "57", "fio": "Дмитриев Дмитрий", "category": "разделка стаж", "rate_month": 3500000, "daily_rate": 116667, "bonus_percent": 20},
    {"id": "58", "fio": "Евгеньев Евгений", "category": "разделка стаж", "rate_month": 3500000, "daily_rate": 116667, "bonus_percent": 20},
    # Қийма
    {"id": "59", "fio": "Жанов Жан", "category": "кийма 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "60", "fio": "Зуфаров Зуфар", "category": "кийма 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "61", "fio": "Игорев Игорь", "category": "кийма 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "62", "fio": "Кириллов Кирилл", "category": "кийма стаж", "rate_month": 3500000, "daily_rate": 116667, "bonus_percent": 20},
    {"id": "63", "fio": "Леонидов Леонид", "category": "кийма стаж", "rate_month": 3500000, "daily_rate": 116667, "bonus_percent": 20},
    {"id": "65", "fio": "Максимов Максим", "category": "кийма 2 кат", "rate_month": 6160000, "daily_rate": 205333, "bonus_percent": 20},
    {"id": "66", "fio": "Николаев Николай", "category": "кийма стаж", "rate_month": 3500000, "daily_rate": 116667, "bonus_percent": 20},
    # Котлет
    {"id": "67", "fio": "Олегов Олег", "category": "котлет 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "68", "fio": "Павлов Павел", "category": "котлет 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "69", "fio": "Романов Роман", "category": "котлет 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "70", "fio": "Сергеев Сергей", "category": "котлет 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    # Филе
    {"id": "71", "fio": "Тимуров Тимур", "category": "филе 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "72", "fio": "Улугбеков Улугбек", "category": "филе 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "73", "fio": "Фарход Фарход", "category": "филе 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "74", "fio": "Хуршидов Хуршид", "category": "филе 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "75", "fio": "Цезарев Цезарь", "category": "филе 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    # Техперсонал
    {"id": "76", "fio": "Чингизов Чингиз", "category": "техперсонал 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "77", "fio": "Шухратов Шухрат", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "78", "fio": "Эдуардов Эдуард", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "79", "fio": "Юрьев Юрий", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "80", "fio": "Ярославов Ярослав", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "81", "fio": "Андреев Андрей", "category": "техперсонал 3 кат", "rate_month": 4900000, "daily_rate": 163333, "bonus_percent": 20},
    {"id": "82", "fio": "Борисов Борис", "category": "техперсонал", "rate_month": 7000000, "daily_rate": 233333, "bonus_percent": 20},
    {"id": "83", "fio": "Владимиров Владимир", "category": "техперсонал 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "84", "fio": "Григорьев Григорий", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "85", "fio": "Денисов Денис", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "86", "fio": "Егоров Егор", "category": "техперсонал 4 кат", "rate_month": 4200000, "daily_rate": 140000, "bonus_percent": 20},
    {"id": "87", "fio": "Женьев Женя", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "88", "fio": "Зоева Зоя", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "89", "fio": "Иванов Иван", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "90", "fio": "Кристинова Кристина", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "91", "fio": "Ларисова Лариса", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "92", "fio": "Маринова Мария", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "93", "fio": "Натальева Наталья", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "94", "fio": "Ольгова Ольга", "category": "техперсонал 5 кат", "rate_month": 3640000, "daily_rate": 121333, "bonus_percent": 20},
    {"id": "95", "fio": "Петров Петр", "category": "техперсонал", "rate_month": 7500000, "daily_rate": 250000, "bonus_percent": 20},
    {"id": "96", "fio": "Ритова Рита", "category": "техперсонал", "rate_month": 5100000, "daily_rate": 170000, "bonus_percent": 20},
    {"id": "97", "fio": "Светланова Светлана", "category": "техперсонал", "rate_month": 4650000, "daily_rate": 155000, "bonus_percent": 20},
    {"id": "98", "fio": "Татьянова Татьяна", "category": "техперсонал", "rate_month": 4650000, "daily_rate": 155000, "bonus_percent": 20},
    {"id": "99", "fio": "Ульянова Ульяна", "category": "техперсонал", "rate_month": 4650000, "daily_rate": 155000, "bonus_percent": 20},
    {"id": "100", "fio": "Федоров Федор", "category": "техперсонал", "rate_month": 4500000, "daily_rate": 150000, "bonus_percent": 20},
    {"id": "101", "fio": "Христинова Христина", "category": "техперсонал", "rate_month": 5270000, "daily_rate": 175667, "bonus_percent": 20},
]

# Ставки по категориям (суточная, фиксированная за день, сум)
DAILY_RATES = {
    "сихлаш 1 кат": 210000,
    "сихлаш 2 кат": 150000,
    "сихлаш 3 кат": 107000,
    "разделка 1 кат": 185000,
    "разделка 2 кат": 145000,
    "разделка 3 кат": 108000,
    "кийма 1 кат": 170000,
    "кийма 2 кат": 140000,
    "кийма 3 кат": 115000,
    "котлет 1 кат": 145000,
    "котлет 2 кат": 120000,
    "котлет 3 кат": 110000,
    "филе 1 кат": 155000,
    "филе 2 кат": 150000,
    "филе 3 кат": 100000,
}

DAILY_PROD = []  # сюда сохраняются все записи производства

# Калибры Go'sht в кг
CALIBER_OPTIONS_KG = [5, 6, 8, 10, 12, 15, 20, 25, 30, 35, 40, 50, 60]

# Чек-лист дисциплины
CHECKLIST_CATEGORIES = [
    {"name": "Санитария и гигиена", "max_points": 20},
    {"name": "Соблюдение технологии", "max_points": 20},
    {"name": "Качество продукции", "max_points": 15},
    {"name": "Производственная дисциплина", "max_points": 15},
    {"name": "Состояние оборудования", "max_points": 10},
    {"name": "Документация и отчётность", "max_points": 10},
    {"name": "Персонал и обучение", "max_points": 10}
]

# Нормы кг по категориям
KG_NORMS = {
    "сихлаш 1 кат": 375,
    "сихлаш 2 кат": 340,
    "сихлаш 3 кат": 300,
    "разделка 1 кат": 250,
    "разделка 2 кат": 220,
    "разделка 3 кат": 200,
    "кийма 1 кат": 180,
    "кийма 2 кат": 160,
    "кийма 3 кат": 140,
    "котлет 1 кат": 120,
    "котлет 2 кат": 110,
    "котлет 3 кат": 100,
    "филе 1 кат": 150,
    "филе 2 кат": 140,
    "филе 3 кат": 130,
}

def calculate_bonus_percent(total_points):
    if total_points >= 90:
        return 100  # 100% бонуса
    elif total_points >= 75:
        return 75
    elif total_points >= 60:
        return 50
    else:
        return 0


@app.route("/")
def index():
    """Главная страница — редирект на табель"""
    return redirect("/tabel")


@app.route("/input", methods=["GET", "POST"])
def input_prod():
    success = None
    error = None

    if request.method == "POST":
        worker_id = request.form.get("worker_id")
        fio = request.form.get("fio")
        product = request.form.get("product")
        quantity = request.form.get("quantity")
        caliber_kg = request.form.get("caliber_kg")
        date = request.form.get("date")

        if not fio or not product or not quantity or not caliber_kg or not date:
            error = "Заполните все поля!"
        else:
            try:
                quantity_pieces = int(quantity)
                selected_caliber_kg = float(caliber_kg)
                quantity_kg = quantity_pieces * selected_caliber_kg

                # Находим работника по ID или ФИО
                worker = next((w for w in WORKERS_TABLE if w["id"] == worker_id or w["fio"] == fio), None)

                if not worker:
                    error = "Ошибка: работник не найден!"
                else:
                    category = worker.get("category", "")
                    daily_rate = worker.get("daily_rate", 0)
                    daily_salary = daily_rate  # фиксированная ставка за день

                    # Расчет нормы и % выполнения
                    norm_kg = KG_NORMS.get(category, 0)
                    percent_complete = (quantity_kg / norm_kg * 100) if norm_kg > 0 else 0

                    # Чек-лист дисциплины
                    checklist_points = {}
                    total_points = 0
                    for i, cat in enumerate(CHECKLIST_CATEGORIES, 1):
                        key = f"checklist_{i}"
                        points = int(request.form.get(key, 0))
                        checklist_points[cat["name"]] = points
                        total_points += points

                    bonus_percent = calculate_bonus_percent(total_points)

                    record = {
                        "worker_id": worker["id"],
                        "fio": fio,
                        "product": product,
                        "quantity_pieces": quantity_pieces,
                        "caliber_kg": selected_caliber_kg,
                        "quantity_kg": round(quantity_kg, 1),
                        "category": category,
                        "daily_rate": daily_rate,
                        "daily_salary": daily_salary,
                        "bonus_percent": bonus_percent,
                        "date": date,
                        "source": "manual",
                        "checklist_points": checklist_points,
                        "total_points": total_points,
                        "norm_kg": norm_kg,
                        "percent_complete": round(percent_complete, 1)
                    }
                    DAILY_PROD.append(record)
                    success = f"Добавлено: {fio} — {quantity_pieces} шт × {selected_caliber_kg} кг = {quantity_kg} кг | З/П: {daily_salary:,} сум"
            except ValueError:
                error = "Ошибка при расчете количества!"

    return render_template("input.html", 
                          products=PRODUCTS, 
                          workers=WORKERS_TABLE,
                          caliber_options=CALIBER_OPTIONS_KG,
                          daily_rates=DAILY_RATES,
                          success=success, 
                          error=error,
                          checklist=CHECKLIST_CATEGORIES,
                          kg_norms=KG_NORMS)




@app.template_filter('format_sum')
def format_sum(value):
    """Форматирует число с пробелами как разделитель тысяч"""
    return "{:,}".format(int(value)).replace(",", " ")


@app.route("/delete/<int:index>")
def delete_record(index):
    """Удаляет запись по индексу"""
    if 0 <= index < len(DAILY_PROD):
        del DAILY_PROD[index]
    return redirect("/tabel")


@app.route("/tabel")
def tabel():
    date_filter = request.args.get("date")
    if date_filter:
        filtered_prod = [r for r in DAILY_PROD if r["date"] == date_filter]
    else:
        filtered_prod = DAILY_PROD
    
    # Рассчитываем итоги за день/фильтр
    total_records = len(filtered_prod)
    total_kg = sum(r.get("quantity_kg", 0) for r in filtered_prod)
    total_salary = sum(r.get("daily_salary", 0) for r in filtered_prod)
    
    # Итого за месяц (все даты)
    monthly_salary = sum(r.get("daily_salary", 0) for r in DAILY_PROD)
    
    total_salary_formatted = "{:,}".format(int(total_salary)).replace(",", " ")
    monthly_salary_formatted = "{:,}".format(int(monthly_salary)).replace(",", " ")
    
    return render_template("tabel.html", 
                          workers=WORKERS_TABLE,
                          daily_prod=filtered_prod,
                          category_rates=DAILY_RATES,
                          total_records=total_records,
                          total_kg=total_kg,
                          total_salary=total_salary,
                          monthly_salary=monthly_salary,
                          total_salary_formatted=total_salary_formatted,
                          monthly_salary_formatted=monthly_salary_formatted)


@app.route("/export")
def export_excel():
    date_filter = request.args.get("date")

    if date_filter:
        filtered = [r for r in DAILY_PROD if r["date"] == date_filter]
        filename = f"tabell_{date_filter}.xlsx"
    else:
        filtered = DAILY_PROD
        filename = "tabell_vse.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "Табель производства"

    # Заголовок
    ws['A1'] = "Табель производства"
    ws.merge_cells('A1:N1')
    ws['A1'].font = Font(bold=True, size=14)

    # Заголовок даты
    ws['A2'] = f"Дата: {date_filter or 'Все даты'}"
    ws.merge_cells('A2:N2')
    ws['A2'].font = Font(size=12)

    # Столбцы
    headers = ["ID", "ФИО", "Товар", "Категория", "Кол-во (шт)", "Калибр (кг)", "Общий вес (кг)", "З/п за смену (сум)", "Баллы всего", "Бонус %", "Норма (кг)", "Выполнено (%)", "Источник", "Дата"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # Данные
    row = 4
    for record in filtered:
        ws.append([
            record.get("worker_id", ""),
            record.get("fio", ""),
            record.get("product", ""),
            record.get("category", ""),
            record.get("quantity_pieces", 0),
            record.get("caliber_kg", 0),
            record.get("quantity_kg", 0),
            record.get("daily_salary", 0),
            record.get("total_points", 0),
            record.get("bonus_percent", 0),
            record.get("norm_kg", 0),
            record.get("percent_complete", 0),
            record.get("source", "Вручную"),
            record.get("date", "")
        ])
        row += 1

    # Итоги
    total_kg = sum(r.get("quantity_kg", 0) for r in filtered)
    total_salary_sum = sum(r.get("daily_salary", 0) for r in filtered)

    ws.append([])
    # Строка итогов должна иметь столько же столбцов, сколько headers
    totals_row_values = [
        "Итого:", "", "", "", "", "",
        total_kg,
        total_salary_sum,
        "", "", "", "", "", ""
    ]
    ws.append(totals_row_values)
    totals_row_index = row + 1
    ws.cell(row=totals_row_index, column=7).font = Font(bold=True)
    ws.cell(row=totals_row_index, column=7).number_format = '#,##0.0'
    ws.cell(row=totals_row_index, column=8).font = Font(bold=True)
    ws.cell(row=totals_row_index, column=8).number_format = '#,##0'

    # Автоширина столбцов
    for col in range(1, len(headers)+1):
        max_length = 0
        column = get_column_letter(col)
        for cell in ws[column]:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    # Отладка
    print("Экспорт: дата фильтра =", date_filter)
    print("Количество записей для экспорта =", len(filtered))

    # Сохраняем в память
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )


@app.route("/monthly_report", methods=["GET", "POST"])
def monthly_report():
    if request.method == "POST":
        month = request.form.get("month")  # формат YYYY-MM
        if not month:
            month = datetime.now().strftime("%Y-%m")

        # Фильтр записей за месяц
        year, mon = map(int, month.split("-"))
        monthly_records = [
            r for r in DAILY_PROD
            if r["date"].startswith(f"{year}-{mon:02d}")
        ]

        # Группировка по категории
        by_category = defaultdict(lambda: {
            "workers": set(),
            "total_kg": 0,
            "total_salary": 0,
            "total_points": 0,
            "count": 0,
            "total_complete": 0
        })

        for r in monthly_records:
            cat = r.get("category", "Неизвестно")
            by_category[cat]["workers"].add(r["worker_id"])
            by_category[cat]["total_kg"] += r.get("quantity_kg", 0)
            by_category[cat]["total_salary"] += r.get("daily_salary", 0)
            by_category[cat]["total_points"] += r.get("total_points", 0)
            by_category[cat]["count"] += 1
            by_category[cat]["total_complete"] += r.get("percent_complete", 0)

        # Итоги по категориям
        categories_report = []
        grand_total_kg = 0
        grand_total_salary = 0
        for cat, data in by_category.items():
            avg_complete = data["total_complete"] / data["count"] if data["count"] > 0 else 0
            avg_bonus = data["total_points"] / data["count"] if data["count"] > 0 else 0
            categories_report.append({
                "category": cat,
                "workers_count": len(data["workers"]),
                "total_kg": round(data["total_kg"], 1),
                "total_salary": int(data["total_salary"]),
                "avg_complete": round(avg_complete, 1),
                "avg_bonus": round(avg_bonus, 1)
            })
            grand_total_kg += data["total_kg"]
            grand_total_salary += data["total_salary"]

        return render_template("monthly_report.html",
                              month=month,
                              categories=categories_report,
                              grand_total_kg=round(grand_total_kg, 1),
                              grand_total_salary=grand_total_salary)

    # GET — форма выбора месяца
    return render_template("monthly_report.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("DEBUG", "False") == "True"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)