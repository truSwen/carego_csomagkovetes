import sys
import sqlite3
import os
import random
import string
from flask import Flask, request, jsonify, g, send_from_directory

# --- Konfiguráció ---
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(APP_ROOT, 'tracker.db')
ADMIN_PASSWORD = "carego_secret_password" 

def init_database():
    """Létrehozza az adatbázis fájlt és a táblákat, ha még nem léteznek."""
    if os.path.exists(DATABASE_PATH):
        print("--- Adatbázis már létezik, inicializálás kihagyva. ---", file=sys.stderr)
        return

    print("--- Adatbázis nem található, INICIALIZÁLÁS MEGKEZDVE... ---", file=sys.stderr)
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE Orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_code TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                recipient_name TEXT,
                address TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE LocationUpdates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_tracking_code TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_tracking_code) REFERENCES Orders (tracking_code)
            )
        ''')
        cursor.execute(
            "INSERT INTO Orders (tracking_code, recipient_name, address, notes, status) VALUES (?, ?, ?, ?, ?)",
            ('TEST123', 'Teszt Elek', '1234 Tesztváros, Próba utca 1.', 'Ez egy alapértelmezett tesztcsomag.', 'felvételre vár')
        )
        conn.commit()
        conn.close()
        print("--- Adatbázis sikeresen inicializálva. ---", file=sys.stderr)
    except Exception as e:
        print(f"!!! HIBA AZ ADATBÁZIS INICIALIZÁLÁSA SORÁN: {e}", file=sys.stderr)

# --- Flask Alkalmazás ---
app = Flask(__name__)
init_database()

# --- Adatbázis Kezelés ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Weboldalak Kiszolgálása ---
@app.route('/')
def serve_customer_app():
    return send_from_directory(APP_ROOT, 'csomagkovetes_v2.html')

@app.route('/courier')
def serve_courier_app():
    return send_from_directory(APP_ROOT, 'courier_app.html')

@app.route('/admin')
def serve_admin_app():
    return send_from_directory(APP_ROOT, 'admin.html')
    
# --- API Végpontok ---
def generate_unique_tracking_code(db):
    while True:
        part1 = ''.join(random.choices(string.ascii_uppercase, k=2))
        part2 = ''.join(random.choices(string.digits, k=2))
        part3 = ''.join(random.choices(string.ascii_uppercase, k=2))
        code = f"CAREGO-{part1}{part2}{part3}"
        cursor = db.cursor()
        cursor.execute("SELECT id FROM Orders WHERE tracking_code = ?", (code,))
        if not cursor.fetchone():
            return code

@app.route('/api/create_order', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or data.get('password') != ADMIN_PASSWORD:
        return jsonify({"status": "error", "message": "Hibás jelszó vagy hiányzó authentikáció."}), 401
    if not all(k in data for k in ['recipient_name', 'address']):
        return jsonify({"status": "error", "message": "Hiányzó adatok: recipient_name és address szükséges."}), 400
    try:
        db = get_db()
        new_code = generate_unique_tracking_code(db)
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO Orders (tracking_code, status, recipient_name, address, notes) VALUES (?, ?, ?, ?, ?)",
            (new_code, 'felvételre vár', data['recipient_name'], data['address'], data.get('notes', ''))
        )
        db.commit()
        return jsonify({"status": "success", "tracking_code": new_code}), 201
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": f"Adatbázis hiba: {e}"}), 500

@app.route('/api/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    if not all(k in data for k in ['tracking_code', 'latitude', 'longitude']):
        return jsonify({"status": "error", "message": "Hiányzó adatok."}), 400
    try:
        db = get_db()
        cursor = db.cursor()
        order = cursor.execute('SELECT id FROM Orders WHERE tracking_code = ?', (data['tracking_code'],)).fetchone()
        if order is None:
            return jsonify({"status": "error", "message": "Követési kód nem létezik."}), 404
        cursor.execute("INSERT INTO LocationUpdates (order_tracking_code, latitude, longitude) VALUES (?, ?, ?)",(data['tracking_code'], data['latitude'], data['longitude']))
        db.commit()
        return jsonify({"status": "success", "message": "Helyzet frissítve"}), 201
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": f"Adatbázis hiba: {e}"}), 500

@app.route('/api/track/<string:tracking_code>', methods=['GET'])
def track_package(tracking_code):
    try:
        db = get_db()
        order = db.execute('SELECT * FROM Orders WHERE tracking_code = ?', (tracking_code,)).fetchone()
        if order is None:
            return jsonify({"status": "error", "message": "A követési kód nem található"}), 404
        last_location = db.execute('SELECT latitude, longitude, timestamp FROM LocationUpdates WHERE order_tracking_code = ? ORDER BY timestamp DESC LIMIT 1',(tracking_code,)).fetchone()
        
        response_data = dict(order)
        response_data["last_known_location"] = dict(last_location) if last_location else None
        
        return jsonify(response_data), 200
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": f"Adatbázis hiba: {e}"}), 500