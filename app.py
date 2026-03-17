from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import csv
import io

app = Flask(__name__)
app.secret_key = '0piso_super_secret_key'
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
        student = conn.execute("SELECT name FROM students WHERE card_uid = ?", (uid,)).fetchone()
        if student:
            # 2. If the student exists, update their balance
            conn.execute("UPDATE students SET balance = balance + ? WHERE card_uid = ?", (amount, uid))
            conn.execute("INSERT INTO transactions (card_uid, amount) VALUES (?, ?)", (uid, amount))
            conn.commit()
            
            # 3. Create the personalized message using the name from the database
            message = f"Top-up Success! P{amount:.2f} added to {student['name']}'s account."
        else:
            # Handle the case where the card isn't registered yet
            message = "Error: Card not found. Please register the card first."
        conn.close()
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

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    # Handle the login form submission
    if request.method == 'POST' and 'username' in request.form:
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['logged_in'] = True
        else:
            error = "Invalid Credentials"

    # If NOT logged in, show the page with the login overlay active
    if not session.get('logged_in'):
        return render_template('admin.html', logged_in=False, error=error, history=[])

    # If logged in, fetch the data
    conn = get_db_connection()
    history = conn.execute('''
        SELECT transactions.timestamp, students.name, transactions.amount 
        FROM transactions 
        JOIN students ON transactions.card_uid = students.card_uid 
        ORDER BY transactions.timestamp DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin.html', logged_in=True, history=history)

if __name__ == '__main__':
    app.run(debug=True)