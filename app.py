from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret_key_here'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload and database directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('instance', exist_ok=True)


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
        c.execute(
            "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
            ('admin@gov', 'admin123', 'admin')
        )

    conn.commit()
    conn.close()


# Initialize database when the Flask application starts
init_db()


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

        c.execute(
            "SELECT * FROM users WHERE email=? AND role=?",
            (email, role)
        )

        user = c.fetchone()

        if user:

            if user[2] == password:

                session['email'] = email
                session['role'] = role

                conn.close()

                if role == 'admin':
                    return redirect('/dashboard')
                else:
                    return redirect('/report')

            else:
                conn.close()
                return "Invalid password"

        else:

            # Auto-register if user doesn't exist and role is user
            if role == 'user':

                c.execute(
                    "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
                    (email, password, role)
                )

                conn.commit()
                conn.close()

                session['email'] = email
                session['role'] = role

                return redirect('/report')

            else:

                conn.close()
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

            image.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    image_filename
                )
            )

        conn = sqlite3.connect('instance/database.db')
        c = conn.cursor()

        c.execute(
            '''INSERT INTO reports
               (title, description, issue_type, location, image_filename)
               VALUES (?, ?, ?, ?, ?)''',
            (
                title,
                description,
                issue_type,
                location,
                image_filename
            )
        )

        conn.commit()
        conn.close()

        return redirect('/success')

    return render_template('report.html')


# Success page
@app.route('/success')
def success():

    if 'email' not in session or session['role'] != 'user':
        return redirect('/login')

    return render_template('success.html')


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

    return render_template(
        'dashboard.html',
        reports=reports
    )


# Mark report as resolved
@app.route('/resolve/<int:report_id>')
def resolve(report_id):

    if 'email' not in session or session['role'] != 'admin':
        return redirect('/login')

    conn = sqlite3.connect('instance/database.db')
    c = conn.cursor()

    c.execute(
        "UPDATE reports SET status='Resolved' WHERE id=?",
        (report_id,)
    )

    conn.commit()
    conn.close()

    return redirect('/dashboard')


# Logout
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# Run application locally
if __name__ == '__main__':
    app.run(debug=True)