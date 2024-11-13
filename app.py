# app.py
#edit
from flask import Flask, render_template, request, redirect, url_for, flash
import json
import uuid
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure random key in production
UPLOAD_FOLDER = 'static/photos/'

def load_entries():
    try:
        with open('entries.json', 'r') as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []
    return entries

def save_entries(entries):
    with open('entries.json', 'w') as f:
        json.dump(entries, f, indent=4)

@app.context_processor
def inject_now():
    return {'current_year': datetime.utcnow().year}

@app.route('/', methods=['GET', 'POST'])
def index():
    entries = load_entries()
    if request.method == 'POST':
        search_query = request.form['search']
        entries = [entry for entry in entries if search_query.lower() in entry['restaurantName'].lower()]
    return render_template('index.html', entries=entries)

@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if request.method == 'POST':
        entries = load_entries()
        filename = ''
        if 'photo' in request.files:
            file = request.files['photo']
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            filename = file.filename
            print(f"File '{file.filename}' saved successfully in the 'photos' directory!")

        print(request.files)

        new_entry = {
            'id': str(uuid.uuid4()),
            'restaurantName': request.form['restaurantName'],
            'mealDescription': request.form['mealDescription'],
            'rating': request.form['rating'],
            'notes': request.form['notes'],
            'location': request.form['location'],
            'photo': filename,
        }
        entries.append(new_entry)
        save_entries(entries)
        flash('Entry added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_entry.html')

@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit_entry(id):
    entries = load_entries()
    entry = next((item for item in entries if item['id'] == id), None)
    if request.method == 'POST':
        entry['restaurantName'] = request.form['restaurantName']
        entry['mealDescription'] = request.form['mealDescription']
        entry['rating'] = request.form['rating']
        entry['notes'] = request.form['notes']
        entry['location'] = request.form['location']
        if 'photo' in request.files:
            file = request.files['photo']
            entry['photo'] = file.filename
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            print(f"File '{file.filename}' saved successfully in the 'photos' directory!")
        print(request.files)

        save_entries(entries)
        flash('Entry updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit_entry.html', entry=entry)

@app.route('/delete/<id>', methods=['POST'])
def delete_entry(id):
    entries = load_entries()
    entries = [entry for entry in entries if entry['id'] != id]
    save_entries(entries)
    flash('Entry deleted successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)