from flask import Flask, render_template, request, session, redirect, url_for, Response
import sqlite3
import csv
import io
import os
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
app.secret_key = 'admin2526'
DB_FILE = 'canteen.db'

# Add Export to .csv button in the main page
# Add Clear Database button in the main page
# Fix logic after pressing buttons

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_local_time():
    # Change 'Asia/Manila' to your specific timezone if different
    tz = pytz.timezone('Asia/Manila')
    return datetime.now(tz).strftime('%Y-%m-%d %I:%M %p')

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
            conn.execute("INSERT INTO students (card_uid, name, balance) VALUES (?, ?, 0.0)", (uid, name))
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
        
        # 1. First, check if the card exists
        student = conn.execute("SELECT * FROM students WHERE card_uid = ?", (uid,)).fetchone()
        
        if not student:
            message = "❌ Error: Card not registered! Please go to Registration."
        
        # 2. If it exists, check the funds
        elif student['balance'] < price:
            message = f"⚠️ Error: Lacking funds! Current balance is only P{student['balance']:.2f}"
            
        # 3. If everything is okay, proceed with payment
        else:
            new_balance = student['balance'] - price
            local_time = get_local_time()
            
            conn.execute("UPDATE students SET balance = ? WHERE card_uid = ?", (new_balance, uid))
            conn.execute("INSERT INTO transactions (card_uid, amount, timestamp) VALUES (?, ?, ?)", 
                         (uid, -price, local_time))
            conn.commit()
            message = f"Payment Successful! New Balance: P{new_balance:.2f}"
        
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
            conn.execute("UPDATE students SET balance = balance + ? WHERE card_uid = ?", (amount, uid))
            local_time = get_local_time()
            conn.execute("INSERT INTO transactions (card_uid, amount, timestamp) VALUES (?, ?, ?)", (uid, amount, local_time))
            
            # --- CRITICAL FIX: Add this line ---
            conn.commit() 
            
            message = f"Top-up Success! P{amount:.2f} added to {student['name']}'s account."
        else:
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

@app.route('/admin.html', methods=['GET', 'POST'])
def admin():
    conn = get_db_connection()
    # Check if admin credentials are set in the database
    admin_config = conn.execute("SELECT * FROM config WHERE key = 'admin_user'").fetchone()
    
    # --- FIRST RUN: SET CREDENTIALS ---
    if not admin_config:
        if request.method == 'POST' and 'new_user' in request.form:
            u = request.form['new_user']
            p = request.form['new_pass']
            conn.execute("INSERT INTO config (key, value) VALUES ('admin_user', ?)", (u,))
            conn.execute("INSERT INTO config (key, value) VALUES ('admin_pass', ?)", (p,))
            conn.commit()
            conn.close()
            return redirect(url_for('admin'))
        return render_template('admin.html', setup_mode=True)

    # --- NORMAL LOGIN LOGIC ---
    error = None
    if request.method == 'POST' and 'username' in request.form:
        stored_user = conn.execute("SELECT value FROM config WHERE key = 'admin_user'").fetchone()['value']
        stored_pass = conn.execute("SELECT value FROM config WHERE key = 'admin_pass'").fetchone()['value']
        
        if request.form['username'] == stored_user and request.form['password'] == stored_pass:
            session['logged_in'] = True
        else:
            error = "Invalid Credentials"

    if not session.get('logged_in'):
        conn.close()
        return render_template('admin.html', logged_in=False, error=error)

    # --- LOAD DATA ---
    history = conn.execute('SELECT t.timestamp, s.name, t.amount FROM transactions t JOIN students s ON t.card_uid = s.card_uid ORDER BY t.timestamp DESC').fetchall()
    conn.close()
    return render_template('admin.html', logged_in=True, history=history)

@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Removes the "logged_in" tag from the session
    return redirect(url_for('index'))

@app.route('/export_csv')
def export_csv():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    
    conn = get_db_connection()
    # Joined query to get the Name instead of just the UID
    cursor = conn.execute('''
        SELECT transactions.timestamp, students.name, transactions.amount 
        FROM transactions 
        JOIN students ON transactions.card_uid = students.card_uid
    ''')
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Student Name', 'Amount (P)']) 
    writer.writerows(cursor.fetchall())
    conn.close()
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=canteen_report.csv"}
    )

@app.route('/wipe_db', methods=['POST'])
def wipe_db():
    if not session.get('logged_in'):
        return redirect(url_for('admin'))
    
    conn = get_db_connection()
    # 1. Delete all data
    conn.execute("DELETE FROM transactions")
    conn.execute("DELETE FROM students")
    
    # 2. Reset the ID counters back to 0
    conn.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='students'")
    
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/change_admin', methods=['POST'])
def change_admin():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    
    new_user = request.form['new_user']
    new_pass = request.form['new_pass']
    
    conn = get_db_connection()
    conn.execute("UPDATE config SET value = ? WHERE key = 'admin_user'", (new_user,))
    conn.execute("UPDATE config SET value = ? WHERE key = 'admin_pass'", (new_pass,))
    conn.commit()
    conn.close()
    
    # Optional: Log them out so they have to login with new credentials
    session.pop('logged_in', None)
    return redirect(url_for('admin'))

@app.context_processor
def inject_version():
    return dict(version="v1.0.0-STABLE")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Create tables if they don't exist
    conn.execute('CREATE TABLE IF NOT EXISTS students (card_uid TEXT PRIMARY KEY, name TEXT, balance REAL)')
    conn.execute('CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, card_uid TEXT, amount REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    # New table for Admin Credentials
    conn.execute('CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)')
    conn.commit()
    conn.close()

init_db()

if __name__ == '__main__':
    app.run(debug=True)