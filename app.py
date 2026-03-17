from flask import Flask, render_template, request, session, redirect, url_for, Response
import sqlite3
import csv
import io

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

@app.route('/admin.html', methods=['GET', 'POST'])
def admin():
    error = None
    
    # --- 1. SET YOUR LOGIN CREDENTIALS HERE ---
    ADMIN_USERNAME = 'admin' 
    ADMIN_PASSWORD = 'admin'

    # Handle Login Attempt
    if request.method == 'POST' and 'username' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
        else:
            error = "Invalid Username or Password"

    # If NOT logged in, show page with Overlay and NO data
    if not session.get('logged_in'):
        return render_template('admin.html', logged_in=False, error=error, history=[])

    # If logged in, fetch the data for the table
    conn = get_db_connection()
    history = conn.execute('''
        SELECT transactions.timestamp, students.name, transactions.amount 
        FROM transactions 
        JOIN students ON transactions.card_uid = students.card_uid 
        ORDER BY transactions.timestamp DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin.html', logged_in=True, history=history)

@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Removes the "logged_in" tag from the session
    return redirect(url_for('index'))

@app.route('/export_csv')
def export_csv():
    if not session.get('logged_in'):
        return redirect(url_for('admin'))
    
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM transactions")
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Card UID', 'Amount', 'Timestamp'])
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

@app.context_processor
def inject_version():
    return dict(version="v0.2.5-BETA")

if __name__ == '__main__':
    app.run(debug=True)