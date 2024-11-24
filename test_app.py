# tests/test_app.py

import pytest
from app import app, load_users, save_users, load_entries, save_entries
from flask import url_for
from flask_login import login_user
from werkzeug.security import generate_password_hash
import json
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with app.test_client() as client:
        with app.app_context():
            # Setup: Reset users.json and entries.json
            save_users({})
            save_entries({})
        yield client
        # Teardown: Clean up after tests
        save_users({})
        save_entries({})

def register(client, username, password):
    return client.post('/register', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

def test_register(client):
    """Test user registration"""
    response = register(client, 'testuser', 'testpassword')
    assert b'Registration successful! You can now log in.' in response.data
    users = load_users()
    assert len(users) == 1
    user = list(users.values())[0]
    assert user['username'] == 'testuser'

def test_login_logout(client):
    """Test user login and logout"""
    register(client, 'testuser', 'testpassword')
    response = login(client, 'testuser', 'testpassword')
    assert b'Logged in successfully.' in response.data
    response = logout(client)
    assert b'You have been logged out.' in response.data

def test_invalid_login(client):
    """Test login with invalid credentials"""
    register(client, 'testuser', 'testpassword')
    response = login(client, 'testuser', 'wrongpassword')
    assert b'Invalid username or password.' in response.data
    response = login(client, 'wronguser', 'testpassword')
    assert b'Invalid username or password.' in response.data

def test_add_entry(client):
    """Test adding a new entry"""
    register(client, 'testuser', 'testpassword')
    login(client, 'testuser', 'testpassword')
    response = client.post('/add', data=dict(
        restaurantName='Test Restaurant',
        mealDescription='Delicious meal',
        rating='5',
        notes='Great experience',
        location='Test Location'
        # Assuming photo upload is optional for testing
    ), follow_redirects=True)
    assert b'Entry added successfully!' in response.data
    entries = load_entries()
    assert len(entries) == 1
    user_entries = entries.get(list(entries.keys())[0], [])
    assert len(user_entries) == 1
    entry = user_entries[0]
    assert entry['restaurantName'] == 'Test Restaurant'
    assert entry['rating'] == '5'

def test_edit_entry(client):
    """Test editing an existing entry"""
    register(client, 'testuser', 'testpassword')
    login(client, 'testuser', 'testpassword')
    client.post('/add', data=dict(
        restaurantName='Test Restaurant',
        mealDescription='Delicious meal',
        rating='5',
        notes='Great experience',
        location='Test Location'
    ), follow_redirects=True)
    entries = load_entries()
    user_id = list(entries.keys())[0]
    entry_id = entries[user_id][0]['id']
    response = client.post(f'/edit/{entry_id}', data=dict(
        restaurantName='Updated Restaurant',
        mealDescription='Even more delicious',
        rating='4',
        notes='Good experience',
        location='Updated Location'
    ), follow_redirects=True)
    assert b'Entry updated successfully!' in response.data
    updated_entry = load_entries()[user_id][0]
    assert updated_entry['restaurantName'] == 'Updated Restaurant'
    assert updated_entry['rating'] == '4'

def test_delete_entry(client):
    """Test deleting an entry"""
    register(client, 'testuser', 'testpassword')
    login(client, 'testuser', 'testpassword')
    client.post('/add', data=dict(
        restaurantName='Test Restaurant',
        mealDescription='Delicious meal',
        rating='5',
        notes='Great experience',
        location='Test Location'
    ), follow_redirects=True)
    entries = load_entries()
    user_id = list(entries.keys())[0]
    entry_id = entries[user_id][0]['id']
    response = client.post(f'/delete/{entry_id}', follow_redirects=True)
    assert b'Entry deleted successfully!' in response.data
    assert len(load_entries()[user_id]) == 0

def test_access_protected_route(client):
    """Test that protected routes require login"""
    response = client.get('/', follow_redirects=True)
    assert b'Please log in to access this page.' in response.data

def test_search_entries(client):
    """Test searching for entries"""
    register(client, 'testuser', 'testpassword')
    login(client, 'testuser', 'testpassword')
    # Add multiple entries
    client.post('/add', data=dict(
        restaurantName='Pizza Place',
        mealDescription='Pepperoni Pizza',
        rating='5',
        notes='Loved it',
        location='New York'
    ), follow_redirects=True)
    client.post('/add', data=dict(
        restaurantName='Burger Joint',
        mealDescription='Cheeseburger',
        rating='4',
        notes='Good',
        location='Los Angeles'
    ), follow_redirects=True)
    # Search for 'Pizza'
    response = client.post('/', data=dict(
        search='Pizza'
    ), follow_redirects=True)
    assert b'Pizza Place' in response.data
    assert b'Burger Joint' not in response.data

def test_duplicate_username(client):
    """Test that duplicate usernames cannot be registered"""
    register(client, 'testuser', 'testpassword')
    response = register(client, 'testuser', 'newpassword')
    assert b'Username already exists. Please choose a different one.' in response.data
    users = load_users()
    assert len(users) == 1  # Still only one user

def test_add_entry_without_login(client):
    """Test that adding an entry requires login"""
    response = client.post('/add', data=dict(
        restaurantName='Test Restaurant',
        mealDescription='Delicious meal',
        rating='5',
        notes='Great experience',
        location='Test Location'
    ), follow_redirects=True)
    assert b'Please log in to access this page.' in response.data
