import sqlite3
import os

def setup_database():
    """Létrehozza a kibővített adatbázist és a szükséges táblákat."""
    # Az adatbázis fájl helyének meghatározása a szkripthez képest
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracker.db')

    try:
        # Csatlakozás az adatbázishoz (létrehozza, ha nem létezik)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Orders (Megrendelések) tábla kibővítése új oszlopokkal
        # A biztonság kedvéért először töröljük a régit, ha létezik, hogy biztosan frissüljön a szerkezet
        cursor.execute('DROP TABLE IF EXISTS Orders')
        cursor.execute('''
            CREATE TABLE Orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_code TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                recipient_name TEXT NOT NULL,
                address TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Az 'Orders' tábla sikeresen létrehozva vagy frissítve.")

        # LocationUpdates tábla létrehozása (ha már létezik, nem bántjuk)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS LocationUpdates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_tracking_code TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_tracking_code) REFERENCES Orders (tracking_code)
            )
        ''')
        print("A 'LocationUpdates' tábla sikeresen létrehozva vagy már létezik.")

        # Tesztadat beszúrása, hogy ne legyen üres az adatbázis
        cursor.execute("SELECT * FROM Orders WHERE tracking_code = 'CAREGO-ADMIN-TEST'")
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO Orders (tracking_code, status, recipient_name, address, notes) 
                VALUES (?, ?, ?, ?, ?)
                """,
                ('CAREGO-ADMIN-TEST', 'felvételre vár', 'Teszt Elek', '1111 Budapest, Teszt utca 1.', 'Óvatosan, törékeny!')
            )
            print("Teszt megrendelés hozzáadva.")

        # Változtatások mentése és kapcsolat bezárása
        conn.commit()
        conn.close()
        print("Adatbázis sikeresen beállítva.")
    except sqlite3.Error as e:
        print(f"Adatbázis hiba: {e}")

if __name__ == '__main__':
    setup_database()

