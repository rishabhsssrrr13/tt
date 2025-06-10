from flask import Flask, request, render_template, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
from rapidfuzz import fuzz  # pip install rapidfuzz
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'  # Change this to a strong random key

# Admin password (change this)
ADMIN_PASSWORD = "Oversmart13"

# Session timeout in seconds (e.g., 10 minutes)
SESSION_TIMEOUT = 10 * 60

# Initialize DB and create tables
def init_db():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            bot_response TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT NOT NULL,
            pattern TEXT NOT NULL,
            response TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Get DB connection
def get_db_connection():
    conn = sqlite3.connect('chat.db')
    conn.row_factory = sqlite3.Row
    return conn

# Log chat messages
def log_chat(user_msg, bot_reply):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO chat_history (user_message, bot_response, timestamp)
        VALUES (?, ?, ?)
    ''', (user_msg, bot_reply, timestamp))
    conn.commit()
    conn.close()

# Find response using fuzzy matching with debug prints
def find_response(user_msg):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT pattern, response FROM intents')
    intents = cursor.fetchall()
    conn.close()

    user_msg_lower = user_msg.lower()
    best_match = None
    highest_score = 0

    # Debug info
    print(f"[DEBUG] User message: '{user_msg_lower}'")

    # Try exact substring match first
    for intent in intents:
        pattern = intent['pattern'].lower()
        if pattern in user_msg_lower or user_msg_lower in pattern:
            print(f"[DEBUG] Exact substring match found: Pattern='{pattern}' Response='{intent['response']}'")
            return intent['response']

    # Else, try fuzzy partial matching
    for intent in intents:
        pattern = intent['pattern'].lower()
        score = fuzz.partial_ratio(user_msg_lower, pattern)
        print(f"[DEBUG] Pattern: '{pattern}', Score: {score}")
        if score > highest_score and score > 50:  # threshold can be tuned
            highest_score = score
            best_match = intent['response']

    print(f"[DEBUG] Best match score: {highest_score}, Response: {best_match}")

    return best_match if best_match else "Sorry, I didn't understand that. कृपया पुनः प्रयास करें।"

# Auto logout logic
@app.before_request
def make_session_permanent():
    if 'admin_logged_in' in session:
        now = datetime.utcnow()
        last_active = session.get('last_active')

        if last_active:
            if isinstance(last_active, str):
                last_active = datetime.strptime(last_active, "%Y-%m-%d %H:%M:%S.%f")
            duration = (now - last_active).total_seconds()
            if duration > SESSION_TIMEOUT:
                session.clear()
                flash("Session timed out. Please log in again.")
                return redirect(url_for("login"))

        session['last_active'] = now.strftime("%Y-%m-%d %H:%M:%S.%f")

# Decorator to protect admin routes
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def chatbot_response():
    msg = request.form.get("msg")
    if not msg:
        return "Please send a message."
    response = find_response(msg)
    log_chat(msg, response)
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['last_active'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
            return redirect(url_for('admin'))
        else:
            flash('Incorrect password. Please try again.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('home'))

@app.route('/admin')
@admin_login_required
def admin():
    conn = get_db_connection()
    intents = conn.execute('SELECT * FROM intents').fetchall()
    conn.close()
    return render_template('admin.html', intents=intents)

@app.route('/add_intent', methods=['POST'])
@admin_login_required
def add_intent():
    tag = request.form['tag'].strip()
    pattern = request.form['pattern'].strip()
    response = request.form['response'].strip()

    if not tag or not pattern or not response:
        flash("Please fill all fields.")
        return redirect(url_for('admin'))

    conn = get_db_connection()
    conn.execute('INSERT INTO intents (tag, pattern, response) VALUES (?, ?, ?)', (tag, pattern, response))
    conn.commit()
    conn.close()
    flash("Intent added successfully!")
    return redirect(url_for('admin'))

@app.route('/delete_intent/<int:intent_id>')
@admin_login_required
def delete_intent(intent_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM intents WHERE id = ?', (intent_id,))
    conn.commit()
    conn.close()
    flash("Intent deleted successfully!")
    return redirect(url_for('admin'))

if __name__ == "__main__":
    app.run(debug=True)
