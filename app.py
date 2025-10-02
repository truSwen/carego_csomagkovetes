from flask import Flask, request, jsonify, g
import sqlite3
import os

app = Flask(__name__)

# Az adatbázis fájl helyének meghatározása az app.py-hoz képest
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracker.db')
# Javaslat: A konfigurációt érdemes egy külön objektumból betölteni a jobb szervezhetőség érdekében.
app.config['DATABASE'] = DATABASE


# --- Adatbázis-kezelés (Javasolt Módosítás) ---

def get_db():
    """
    Létrehoz egy adatbázis-kapcsolatot, ha még nem létezik az aktuális kéréshez.
    A Flask 'g' globális objektumát használjuk a kapcsolat tárolására,
    így a kapcsolat a kérés teljes élettartama alatt elérhető lesz.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """
    Automatikusan lezárja az adatbázis-kapcsolatot a kérés végén,
    függetlenül attól, hogy sikeres volt-e vagy hiba történt.
    Ez egy sokkal biztonságosabb és tisztább megoldás.
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# --- API Végpontok ---

@app.route('/api/update_location', methods=['POST'])
def update_location():
    """A futár app ezen a végponton keresztül küldi el a helyzetét."""
    data = request.get_json()
    
    # Részletesebb validáció
    if not data or not all(k in data for k in ['tracking_code', 'latitude', 'longitude']):
        return jsonify({"status": "error", "message": "Missing data: tracking_code, latitude, or longitude"}), 400

    tracking_code = data['tracking_code']
    latitude = data['latitude']
    longitude = data['longitude']

    # Javaslat: Adattípus ellenőrzése
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return jsonify({"status": "error", "message": "Latitude and longitude must be numbers"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO LocationUpdates (order_tracking_code, latitude, longitude) VALUES (?, ?, ?)",
            (tracking_code, latitude, longitude)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Location update received"}), 201
    
    # Javaslat: Specifikusabb hibakezelés
    except sqlite3.IntegrityError:
        # Ez a hiba akkor fordul elő, ha a `tracking_code` nem létezik az `Orders` táblában
        # (feltéve, ha van FOREIGN KEY megkötés a DB sémában)
        return jsonify({"status": "error", "message": f"Invalid tracking_code: {tracking_code} does not exist."}), 404
    except sqlite3.Error as e:
        # Minden más adatbázis hiba
        # Fontos: Éles környezetben a konkrét hibaüzenetet (e) érdemes logolni, nem a kliensnek visszaküldeni.
        app.logger.error(f"Database error on location update: {e}")
        return jsonify({"status": "error", "message": "Database error occurred"}), 500


@app.route('/api/track/<string:tracking_code>', methods=['GET'])
def track_package(tracking_code):
    """A kliens ezen a végponton keresztül követheti a csomagot."""
    try:
        conn = get_db() # A továbbfejlesztett get_db() függvény használata

        # Megrendelés adatainak lekérdezése
        order = conn.execute('SELECT * FROM Orders WHERE tracking_code = ?', (tracking_code,)).fetchone()

        if order is None:
            return jsonify({"status": "error", "message": "Tracking code not found"}), 404

        # Utolsó helyzet lekérdezése
        last_location = conn.execute(
            'SELECT latitude, longitude, timestamp FROM LocationUpdates WHERE order_tracking_code = ? ORDER BY timestamp DESC LIMIT 1',
            (tracking_code,)
        ).fetchone()

        # A conn.close() hívásra már nincs szükség, az @app.teardown_appcontext elintézi.

        response_data = {
            "tracking_code": order['tracking_code'],
            "status": order['status'],
            "created_at": order['created_at'],
            "last_known_location": None
        }

        if last_location:
            response_data["last_known_location"] = {
                "latitude": last_location['latitude'],
                "longitude": last_location['longitude'],
                "timestamp": last_location['timestamp']
            }

        return jsonify(response_data), 200

    except sqlite3.Error as e:
        app.logger.error(f"Database error on tracking package {tracking_code}: {e}")
        return jsonify({"status": "error", "message": "Database error occurred"}), 500


if __name__ == '__main__':
    # Ellenőrizzük, hogy az adatbázis létezik-e, mielőtt a szerver elindul
    if not os.path.exists(app.config['DATABASE']):
        print(f"Hiba: Az adatbázis ('{app.config['DATABASE']}') nem található.")
        print("Kérlek, futtasd a 'database_setup.py' szkriptet először.")
    else:
        # Figyelem: A debug=True módot soha ne használd éles (production) környezetben!
        app.run(host='0.0.0.0', port=5000, debug=True)
