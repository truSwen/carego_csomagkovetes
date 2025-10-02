import sqlite3
import os

def seed_data():
    """Feltölti az adatbázist egy teszt megrendeléssel."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracker.db')

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ellenőrizzük, hogy a teszt adat már létezik-e
        cursor.execute("SELECT * FROM Orders WHERE tracking_code = 'TEST123'")
        if cursor.fetchone():
            print("A 'TEST123' követési kódú teszt megrendelés már létezik.")
        else:
            # Teszt megrendelés beszúrása
            cursor.execute(
                "INSERT INTO Orders (tracking_code, status) VALUES (?, ?)",
                ('TEST123', 'folyamatban')
            )
            conn.commit()
            print("A 'TEST123' követési kódú teszt megrendelés sikeresen hozzáadva.")

        conn.close()
    except sqlite3.Error as e:
        print(f"Adatbázis hiba: {e}")

if __name__ == '__main__':
    seed_data()