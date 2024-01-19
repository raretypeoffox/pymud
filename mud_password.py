# mud_password.py

import hashlib
import os
import sqlite3

from mud_consts import DATABASE_FOLDER, USER_DATABASE

# Global connection and cursor
conn = sqlite3.connect(DATABASE_FOLDER + "/" + USER_DATABASE)
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password BLOB
    )
''')

def hash_password(password):
    salt = os.urandom(32) # A new salt for this user
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + hashed

def save_password(username, password):
    hashed_password = hash_password(password)
    cursor.execute('INSERT INTO users VALUES (?, ?)', (username.lower(), hashed_password))
    conn.commit()

def load_password(username):
    cursor.execute('SELECT password FROM users WHERE username = ?', (username.lower(),))
    result = cursor.fetchone()
    return result[0] if result else None

def verify_password(stored_password, provided_password):
    salt = stored_password[:32] # 32 is the length of the salt
    stored_password = stored_password[32:]
    hashed = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return hashed == stored_password