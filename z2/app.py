from flask import Flask, render_template, request
import mysql.connector
from datetime import datetime,timedelta
from calendar import month_name


app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="Electric_Bill" 
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/bill", methods=["POST"])
def bill():
    bill_month = request.form.get("month")  
    bill_year = request.form.get("year")  

    if not (bill_month and bill_year):
        return "Please provide both month and year!"

    bill_date = datetime(int(bill_year), int(bill_month), 1)
    prev_date = bill_date - timedelta(days=1)  

    con = get_db()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        SELECT * FROM BILL
        WHERE MONTH(`ts`) = %s AND YEAR(`ts`) = %s
        LIMIT 1
    """, (bill_date.month, bill_date.year))
    bill = cur.fetchone()

    if not bill:
        con.close()
        return "Bill not found for given month and year."

    cur.execute("""
        SELECT 
            DATE_FORMAT(`ts`, '%Y-%m') AS bill_month,
            SUM(`DAILY CONSUMPTION`) AS total_units,
            SUM(KVA) AS total_kva,
            SUM(`TOTAL RATE`) AS total_rate
        FROM BILL
        WHERE YEAR(`ts`) = %s
        GROUP BY bill_month
        ORDER BY bill_month ASC
    """, (bill_date.year,))
    billing_history = cur.fetchall()

    cur.execute("""
        SELECT 
            SUM(KWH) AS kwh,
            SUM(KVA) AS kva,
            SUM(KW) AS kw
        FROM BILL
        WHERE MONTH(`ts`) = %s AND YEAR(`ts`) = %s
    """, (bill_date.month, bill_date.year))
    current = cur.fetchone()

    cur.execute("""
        SELECT 
            SUM(KWH) AS kwh,
            SUM(KVA) AS kva,
            SUM(KW) AS kw
        FROM BILL
        WHERE MONTH(`ts`) = %s AND YEAR(`ts`) = %s
    """, (prev_date.month, prev_date.year))
    previous = cur.fetchone()

    con.close()

    def safe_val(d, key):
        return d.get(key) if d and d.get(key) is not None else 0

    def safe_diff(curr_val, prev_val):
        return curr_val - prev_val

    consumption_rows = [
        {
            "label": "Current",
            "date": bill_date.strftime("%d/%m/%Y"),
            "KWH": safe_val(current, "kwh"),
            "KVA": safe_val(current, "kva"),
            "KW": safe_val(current, "kw"),
        },
        {
            "label": "Previous",
            "date": prev_date.strftime("%d/%m/%Y"),
            "KWH": safe_val(previous, "kwh"),
            "KVA": safe_val(previous, "kva"),
            "KW": safe_val(previous, "kw"),
        },
        {
            "label": "Difference",
            "date": prev_date.strftime("%d/%m/%Y"),
            "KWH": safe_diff(safe_val(current, "kwh"), safe_val(previous, "kwh")),
            "KVA": safe_diff(safe_val(current, "kva"), safe_val(previous, "kva")),
            "KW": safe_diff(safe_val(current, "kw"), safe_val(previous, "kw")),
        },
    ]

    return render_template("bill.html",
                           bill=bill,
                           billing_history=billing_history,
                           consumption_rows=consumption_rows)

if __name__ == "__main__":
    app.run(debug=True)