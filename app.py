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
    # Сихлаш
    {"id": "1", "fio": "Alimov Murod", "category": "4 категория", "oklad": 4200000},
    {"id": "2", "fio": "Aliqulov Diyor", "category": "5 категория", "oklad": 3640000},
    {"id": "3", "fio": "Balqiboev Asadbek", "category": "4 категория", "oklad": 4200000},
    {"id": "4", "fio": "Balqiboev Temur", "category": "2 категория", "oklad": 6160000},
    {"id": "5", "fio": "Boboqulov Ma'rufjon", "category": "4 категория", "oklad": 4200000},
    {"id": "6", "fio": "Botiraliyev Iskandar", "category": "4 категория", "oklad": 4200000},
    {"id": "7", "fio": "Botirov Ulug'bek", "category": "4 категория", "oklad": 4200000},
    {"id": "8", "fio": "Hakimov Islom", "category": "2 категория", "oklad": 6160000},
    {"id": "9", "fio": "Ibragimov Ozodbek", "category": "3 категория", "oklad": 4900000},
    {"id": "10", "fio": "Jonizaqov Xasanjon", "category": "4 категория", "oklad": 4200000},
    {"id": "11", "fio": "Jonizaqov Xusanjon", "category": "4 категория", "oklad": 4200000},
    {"id": "12", "fio": "Keldibekov Muxammadkodir", "category": "2 категория", "oklad": 6160000},
    {"id": "13", "fio": "Kuchkinov Abdulaziz", "category": "2 категория", "oklad": 6160000},
    {"id": "14", "fio": "Lapasov Javohir", "category": "4 категория", "oklad": 4200000},
    {"id": "15", "fio": "Maxkamov Jahongir", "category": "стаж", "oklad": 3500000},
    {"id": "16", "fio": "Miraliev Mirxasan", "category": "2 категория", "oklad": 6160000},
    {"id": "17", "fio": "Miraliev Mirxusan", "category": "4 категория", "oklad": 4200000},
    {"id": "18", "fio": "Muxammadiev Abbos", "category": "2 категория", "oklad": 6160000},
    {"id": "19", "fio": "Nazarov Abdukodir", "category": "2 категория", "oklad": 6160000},
    {"id": "20", "fio": "Nishonov Maxmudjon", "category": "1 категория", "oklad": 6440000},
    {"id": "21", "fio": "Normatov Avazbek", "category": "3 категория", "oklad": 4900000},
    {"id": "22", "fio": "O'ktamov Sardor", "category": "4 категория", "oklad": 4200000},
    {"id": "23", "fio": "Olimxonov Nurmuhammad", "category": "5 категория", "oklad": 3640000},
    {"id": "24", "fio": "Ortiqboev Ma'rufjon", "category": "4 категория", "oklad": 4200000},
    {"id": "25", "fio": "Qo'chqorov Sardor", "category": "2 категория", "oklad": 6160000},
    {"id": "26", "fio": "Qo'shbokov Inomjon", "category": "3 категория", "oklad": 4900000},
    {"id": "27", "fio": "Raimberdiyev Dilshod", "category": "5 категория", "oklad": 3640000},
    {"id": "28", "fio": "Rustamjonov Aziz", "category": "4 категория", "oklad": 4200000},
    {"id": "29", "fio": "Sattorov Ulug'bek", "category": "5 категория", "oklad": 3640000},
    {"id": "30", "fio": "Shermatov Javlon", "category": "2 категория", "oklad": 6160000},
    {"id": "31", "fio": "Tashmatov Raximjon", "category": "5 категория", "oklad": 3640000},
    {"id": "32", "fio": "To'xtamurodov Izzatilla", "category": "4 категория", "oklad": 4200000},
    {"id": "33", "fio": "Tugalov Sherzod", "category": "3 категория", "oklad": 4900000},
    {"id": "34", "fio": "Vaxobjonov Avazbek", "category": "5 категория", "oklad": 3640000},
    {"id": "35", "fio": "Xalilov Nodirbek", "category": "1 категория", "oklad": 6440000},
    {"id": "36", "fio": "Xapizov Ozodbek", "category": "5 категория", "oklad": 3640000},
    {"id": "37", "fio": "Xayrullaev Jasurbek", "category": "3 категория", "oklad": 4900000},
    {"id": "38", "fio": "Xoliqov Jumanazarbek", "category": "3 категория", "oklad": 4900000},
    {"id": "39", "fio": "Maxmudova Muslima", "category": "5 категория", "oklad": 3640000},
    {"id": "40", "fio": "Obidov Ziyodulla", "category": "3 категория", "oklad": 4900000},
    {"id": "41", "fio": "Turg'unboyev Asadbek", "category": "стаж", "oklad": 3500000},

    # Разделка
    {"id": "42", "fio": "Abdullayev Sherzod", "category": "5 категория", "oklad": 3640000},
    {"id": "43", "fio": "Abduvaliyev Yaxyo", "category": "5 категория", "oklad": 3640000},
    {"id": "44", "fio": "Bo'riqulov Shaxzod", "category": "2 категория", "oklad": 6160000},
    {"id": "45", "fio": "Keldiev Azizbek", "category": "4 категория", "oklad": 4200000},
    {"id": "46", "fio": "Xurramov Shamsiddin", "category": "4 категория", "oklad": 4200000},
    {"id": "47", "fio": "Abdulxamidov Xasan", "category": "1 категория", "oklad": 6440000},
    {"id": "48", "fio": "Eshmurodov Mirzoxid", "category": "2 категория", "oklad": 6160000},
    {"id": "49", "fio": "Kamilov Rustam", "category": "4 категория", "oklad": 4200000},
    {"id": "50", "fio": "Mirzakulov Mirolim", "category": "1 категория", "oklad": 6440000},
    # ... и так далее для остальных цехов (если нужно — добавь сам или скажи, я продолжу)

    # Добавь остальных по аналогии
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
    "1 категория": 214667,
    "2 категория": 205333,
    "3 категория": 163333,
    "4 категория": 140000,
    "5 категория": 121333,
    "стаж": 116667,
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
    "1 категория": 375,
    "2 категория": 340,
    "3 категория": 300,
    "4 категория": 250,
    "5 категория": 140,
    "стаж": 300,
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
                    daily_rate = DAILY_RATES.get(category, 0)
                    daily_salary = daily_rate  # фиксированная ставка за день

                    # Расчет нормы и % выполнения
                    norm_kg = KG_NORMS.get(category, 0)
                    percent_complete = (quantity_kg / norm_kg * 100) if norm_kg > 0 else 0

                    # Расчет коэффициента з/п и бонуса по норме
                    if percent_complete >= 90:
                        salary_coeff = 1.0
                        if percent_complete >= 100:
                            bonus_percent = 20
                        elif percent_complete >= 80:
                            bonus_percent = 10
                        else:
                            bonus_percent = 0
                    elif percent_complete >= 80:
                        salary_coeff = 0.9
                        bonus_percent = 0
                    elif percent_complete >= 70:
                        salary_coeff = 0.7
                        bonus_percent = 0
                    else:
                        salary_coeff = 0.5
                        bonus_percent = 0

                    daily_salary = int(daily_rate * salary_coeff)

                    full_salary = daily_rate  # полная ставка без коэффициента
                    reduced_amount = full_salary - daily_salary  # сколько урезано

                    # Чек-лист дисциплины
                    checklist_points = {}
                    total_points = 0
                    for i, cat in enumerate(CHECKLIST_CATEGORIES, 1):
                        key = f"checklist_{i}"
                        points = int(request.form.get(key, 0))
                        checklist_points[cat["name"]] = points
                        total_points += points

                    record = {
                        "worker_id": worker["id"],
                        "fio": fio,
                        "product": product,
                        "quantity_pieces": quantity_pieces,
                        "caliber_kg": selected_caliber_kg,
                        "quantity_kg": round(quantity_kg, 1),
                        "category": category,
                        "daily_rate": daily_rate,
                        "salary_coeff": salary_coeff,
                        "daily_salary": daily_salary,
                        "full_salary": full_salary,
                        "reduced_amount": reduced_amount,
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
    headers = ["ID", "ФИО", "Товар", "Категория", "Кол-во (шт)", "Калибр (кг)", "Общий вес (кг)", "З/п полная (сум)", "З/п за смену (сум)", "Урезано (сум)", "Коэф. з/п", "Баллы всего", "Бонус %", "Норма (кг)", "Выполнено (%)", "Источник", "Дата"]
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
            record.get("full_salary", 0),
            record.get("daily_salary", 0),
            record.get("reduced_amount", 0),
            record.get("salary_coeff", 1.0),
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
    total_full_salary = sum(r.get("full_salary", 0) for r in filtered)
    total_salary_sum = sum(r.get("daily_salary", 0) for r in filtered)
    total_reduced = sum(r.get("reduced_amount", 0) for r in filtered)

    ws.append([])
    # Строка итогов должна иметь столько же столбцов, сколько headers
    totals_row_values = [
        "Итого:", "", "", "", "", "",
        total_kg,
        total_full_salary,
        total_salary_sum,
        total_reduced,
        "", "", "", "", "", "", ""
    ]
    ws.append(totals_row_values)
    totals_row_index = row + 1
    ws.cell(row=totals_row_index, column=7).font = Font(bold=True)
    ws.cell(row=totals_row_index, column=7).number_format = '#,##0.0'
    ws.cell(row=totals_row_index, column=8).font = Font(bold=True)
    ws.cell(row=totals_row_index, column=8).number_format = '#,##0'
    ws.cell(row=totals_row_index, column=9).font = Font(bold=True)
    ws.cell(row=totals_row_index, column=9).number_format = '#,##0'
    ws.cell(row=totals_row_index, column=10).font = Font(bold=True)
    ws.cell(row=totals_row_index, column=10).number_format = '#,##0'

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
