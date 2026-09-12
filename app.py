from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret_key_here'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize the database
def init_db():
    conn = sqlite3.connect('instance/database.db')
    c = conn.cursor()

    # Create reports table
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    issue_type TEXT,
                    location TEXT,
                    image_filename TEXT,
                    status TEXT DEFAULT 'Pending'
                )''')

    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password TEXT,
                    role TEXT
                )''')

    # Add default admin if not exists
    c.execute("SELECT * FROM users WHERE email='admin@gov'")
    if not c.fetchone():
        c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
                  ('admin@gov', 'admin123', 'admin'))

    conn.commit()
    conn.close()

# Home route
@app.route('/')
def home():
    return redirect('/login')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = sqlite3.connect('instance/database.db')
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE email=? AND role=?", (email, role))
        user = c.fetchone()

        if user:
            if user[2] == password:
                session['email'] = email
                session['role'] = role
                return redirect('/dashboard' if role == 'admin' else '/report')
            else:
                return "Invalid password"
        else:
            # Auto-register if user doesn't exist and role is 'user'
            if role == 'user':
                c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (email, password, role))
                conn.commit()
                conn.close()
                session['email'] = email
                session['role'] = role
                return redirect('/report')
            else:
                return "Invalid credentials and role selected"
    return render_template('login.html')

# Report route
@app.route('/report', methods=['GET', 'POST'])
def report():
    if 'email' not in session or session['role'] != 'user':
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        issue_type = request.form['issue_type']
        location = request.form['location']
        image = request.files['image']

        image_filename = None
        if image and image.filename != '':
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        conn = sqlite3.connect('instance/database.db')
        c = conn.cursor()
        c.execute('''INSERT INTO reports (title, description, issue_type, location, image_filename)
                     VALUES (?, ?, ?, ?, ?)''',
                  (title, description, issue_type, location, image_filename))
        conn.commit()
        conn.close()

        return "✅ Report submitted successfully! <a href='/report'>Submit Another</a> | <a href='/logout'>Logout</a>"
    return render_template('report.html')

# Admin dashboard
@app.route('/dashboard')
def dashboard():
    if 'email' not in session or session['role'] != 'admin':
        return redirect('/login')

    conn = sqlite3.connect('instance/database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reports")
    reports = c.fetchall()
    conn.close()
    return render_template('dashboard.html', reports=reports)

# Mark report as resolved
@app.route('/resolve/<int:report_id>')
def resolve(report_id):
    if 'email' not in session or session['role'] != 'admin':
        return redirect('/login')

    conn = sqlite3.connect('instance/database.db')
    c = conn.cursor()
    c.execute("UPDATE reports SET status='Resolved' WHERE id=?", (report_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
