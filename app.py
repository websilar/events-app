from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            cost REAL NOT NULL,
            available_places INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            places INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    ''')

    conn.commit()
    conn.close()


DATABASE = 'database.db'

create_tables()

login_manager = LoginManager()
login_manager.init_app(app)






# User loader for Flask-Login
class User(UserMixin):
    def __init__(self, id_, email):
        self.id = id_
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return User(user[0], user[1]) if user else None

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            login_user(User(user[0], email))
            return redirect(url_for('events'))
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = generate_password_hash(request.form['password'])
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
    conn.commit()
    conn.close()
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/events')
@login_required
def events():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, date, cost, available_places FROM events ORDER BY date ASC")
    events = cursor.fetchall()
    conn.close()
    return render_template('events.html', events=events)

@app.route('/event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def event_detail(event_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, date, cost, available_places FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        places = int(request.form['places'])
        total_cost = event[4] * places

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO bookings (user_id, event_id, places, total_cost) VALUES (?, ?, ?, ?)",
                       (session['_user_id'], event_id, places, total_cost))
        cursor.execute("UPDATE events SET available_places = available_places - ? WHERE id = ?", (places, event_id))
        conn.commit()
        conn.close()
        return redirect(url_for('events'))

    return render_template('event_detail.html', event=event)

if __name__ == '__main__':
    
    app.run(debug=True)