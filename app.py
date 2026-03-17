from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB_FILE = 'canteen.db'

# Add Export to .csv button in the main page
# Add Clear Database button in the main page
# Fix logic after pressing buttons

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index.html')
def home():
    return render_template('index.html')

@app.route('/register.html', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        uid = request.form['uid']
        name = request.form['name']
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO students (card_uid, name, balance) VALUES (?, ?, 0)", (uid, name))
            conn.commit()
            message = f"Success: {name} registered with ID {uid}."
        except sqlite3.IntegrityError:
            message = "Error: This card is already registered."
        finally:
            conn.close()
    return render_template('register.html', message=message)

@app.route('/payment.html', methods=['GET', 'POST'])
def payment():
    message = None
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
            message = f"Success! New Balance: P{new_balance}" # Set the success message
        else:
            message = "Error: Insufficient funds or card not found!" # Set the error message
        conn.close()
    return render_template('payment.html', message=message)

@app.route('/topup.html', methods=['GET', 'POST'])
def topup():
    message = None
    if request.method == 'POST':
        uid = request.form['uid']
        amount = float(request.form['amount'])
        conn = get_db_connection()
        conn.execute("UPDATE students SET balance = balance + ? WHERE card_uid = ?", (amount, uid))
        conn.execute("INSERT INTO transactions (card_uid, amount) VALUES (?, ?)", (uid, amount))
        conn.commit()
        conn.close()
        message = f"Top-up Success! P{amount} added to card {uid}."
    return render_template('topup.html', message=message)

@app.route('/check_balance.html', methods=['GET', 'POST'])
def check_balance():
    message = None
    if request.method == 'POST':
        uid = request.form['uid']
        conn = get_db_connection()
        student = conn.execute("SELECT * FROM students WHERE card_uid = ?", (uid,)).fetchone()
        conn.close()
        if student:
            message = f"Name: {student['name']} | Current Balance: P{student['balance']}"
        else:
            message = "Error: Card not found."
    return render_template('check_balance.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)