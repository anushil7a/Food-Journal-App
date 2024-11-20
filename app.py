# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import json
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure random key in production
UPLOAD_FOLDER = 'static/photos/'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if not authenticated

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    user = users.get(user_id)
    if user:
        return User(user_id, user['username'], user['password_hash'])
    return None

# Extracts the map's src to use in the template
def extract_location_src(html_string):
    """
    Extracts the src path from an HTML-like string or returns the whole string if src is missing.

    Args:
        html_string (str): The input HTML-like string.

    Returns:
        str: The src path if found, otherwise the input string.
    """
    match = re.search(r'src=["\'](.*?)["\']', html_string)
    return match.group(1) if match else html_string


# Function to load users from JSON file
def load_users():
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = {}
    return users

# Function to save users to JSON file
def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

# Function to load entries from JSON file
def load_entries():
    try:
        with open('entries.json', 'r') as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        entries = {}  # Initialize as an empty dictionary
    return entries

# Function to save entries to JSON file
def save_entries(entries):
    with open('entries.json', 'w') as f:
        json.dump(entries, f, indent=4)

@app.context_processor
def inject_now():
    return {'current_year': datetime.utcnow().year}

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        if any(user['username'] == username for user in users.values()):
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        users[user_id] = {'username': username, 'password_hash': password_hash}
        save_users(users)
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']

        # Find user by username
        for user_id, user in users.items():
            if user['username'] == username:
                if check_password_hash(user['password_hash'], password):
                    user_obj = User(user_id, username, user['password_hash'])
                    login_user(user_obj)
                    flash('Logged in successfully.', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Invalid username or password.', 'danger')
                    return redirect(url_for('login'))
        flash('Invalid username or password.', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Home page route
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    entries = load_entries()
    user_entries = entries.get(current_user.id, [])
    if request.method == 'POST':
        search_query = request.form['search']
        user_entries = [entry for entry in user_entries if search_query.lower() in entry['restaurantName'].lower()]
    for entry in user_entries:
        entry['location'] = extract_location_src(entry['location'])
    print(user_entries)
    return render_template('index.html', entries=user_entries)

# Add entry route
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_entry():
    if request.method == 'POST':
        entries = load_entries()
        user_entries = entries.get(current_user.id, [])
        filename = ''
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename != '':
                filename = file.filename.replace(' ', '_')
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                print(f"File '{filename}' saved successfully in the 'photos' directory!")

        new_entry = {
            'id': str(uuid.uuid4()),
            'restaurantName': request.form['restaurantName'],
            'mealDescription': request.form['mealDescription'],
            'rating': request.form['rating'],
            'notes': request.form['notes'],
            'location': request.form['location'],
            'photo': filename,
        }
        user_entries.append(new_entry)
        entries[current_user.id] = user_entries
        save_entries(entries)
        flash('Entry added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_entry.html')

# Edit entry route
@app.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_entry(id):
    entries = load_entries()
    user_entries = entries.get(current_user.id, [])
    entry = next((item for item in user_entries if item['id'] == id), None)
    if not entry:
        flash('Entry not found.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        entry['restaurantName'] = request.form['restaurantName']
        entry['mealDescription'] = request.form['mealDescription']
        entry['rating'] = request.form['rating']
        entry['notes'] = request.form['notes']
        entry['location'] = request.form['location']
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename != '':
                filename = file.filename.replace(' ', '_')
                entry['photo'] = filename
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                print(f"File '{filename}' saved successfully in the 'photos' directory!")
        save_entries(entries)
        flash('Entry updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit_entry.html', entry=entry)

# Delete entry route
@app.route('/delete/<id>', methods=['POST'])
@login_required
def delete_entry(id):
    entries = load_entries()
    user_entries = entries.get(current_user.id, [])
    user_entries = [entry for entry in user_entries if entry['id'] != id]
    entries[current_user.id] = user_entries
    save_entries(entries)
    flash('Entry deleted successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)