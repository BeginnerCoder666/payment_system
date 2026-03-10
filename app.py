from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB_FILE = 'canteen.db'
# NI-
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn
#ballsacks yes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uid = request.form['uid']
        name = request.form['name']
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO students (card_uid, name, balance) VALUES (?, ?, 0)", (uid, name))
            conn.commit()
            return "Registration Successful! <a href='/register'>Back</a>"
        except sqlite3.IntegrityError:
            return "Error: Card already registered! <a href='/register'>Back</a>"
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        uid = request.form['uid']
        price = float(request.form['price'])
        conn = get_db_connection()
        student = conn.execute("SELECT * FROM students WHERE card_uid = ?", (uid,)).fetchone()
        
        if student and student['balance'] >= price:
            new_balance = student['balance'] - price
            conn.execute("UPDATE students SET balance = ? WHERE card_uid = ?", (new_balance, uid))
            conn.execute("INSERT INTO transactions (card_uid, amount) VALUES (?, ?)", (uid, -price))
            conn.commit()
            conn.close()
            return f"Success! Remaining: P{new_balance} <a href='/payment'>Back</a>"
        conn.close()
        return "Error: Insufficient funds or card not found! <a href='/payment'>Back</a>"
    return render_template('payment.html')

@app.route('/topup', methods=['GET', 'POST'])
def topup():
    if request.method == 'POST':
        uid = request.form['uid']
        amount = float(request.form['amount'])
        conn = get_db_connection()
        conn.execute("UPDATE students SET balance = balance + ? WHERE card_uid = ?", (amount, uid))
        conn.execute("INSERT INTO transactions (card_uid, amount) VALUES (?, ?)", (uid, amount))
        conn.commit()
        conn.close()
        return "Top-up Successful! <a href='/topup'>Back</a>"
    return render_template('topup.html')

@app.route('/check_balance', methods=['GET', 'POST'])
def check_balance():
    if request.method == 'POST':
        uid = request.form['uid']
        conn = get_db_connection()
        student = conn.execute("SELECT * FROM students WHERE card_uid = ?", (uid,)).fetchone()
        conn.close()
        if student:
            return f"Student: {student['name']} | Balance: P{student['balance']} <a href='/check_balance'>Back</a>"
        return "Card not found! <a href='/check_balance'>Back</a>"
    return render_template('check_balance.html')

if __name__ == '__main__':
    app.run(debug=True)