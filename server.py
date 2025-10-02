    import sys
    import os
    from flask import Flask, send_from_directory, jsonify

    # --- DIAGNOSZTIKA ---
    # Ezt a részt a hibakeresés után törölhetjük
    print("--- DIAGNOSZTIKAI SZERVER INDUL ---", file=sys.stderr)
    try:
        # Kiírjuk a jelenlegi munkafolyamatot
        CWD = os.getcwd()
        print(f"Jelenlegi munkafolyamat (CWD): {CWD}", file=sys.stderr)

        # Kiírjuk a számított gyökérmappát
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        print(f"Számított __file__ alapján APP_ROOT: {APP_ROOT}", file=sys.stderr)
        
        # Listázzuk a CWD mappa tartalmát
        print("--- A JELENLEGI MAPPA TARTALMA ---", file=sys.stderr)
        for item in os.listdir(CWD):
            print(f"- {item}", file=sys.stderr)
        print("--- TARTALOM VÉGE ---", file=sys.stderr)

    except Exception as e:
        print(f"!!! HIBA A DIAGNOSZTIKAI RÉSZBEN: {e}", file=sys.stderr)
    # --- DIAGNOSZTIKA VÉGE ---


    app = Flask(__name__)
    
    # A fájlokat a jelenlegi munkafolyamatból próbáljuk kiszolgálni
    FILE_DIRECTORY = os.getcwd()

    @app.route('/')
    def serve_customer_app():
        print("Kérés érkezett a '/' (főoldal) végpontra.", file=sys.stderr)
        try:
            print(f"Kísérlet: 'csomagkovetes_v2.html' kiszolgálása innen: {FILE_DIRECTORY}", file=sys.stderr)
            return send_from_directory(FILE_DIRECTORY, 'csomagkovetes_v2.html')
        except Exception as e:
            print(f"!!! HIBA a '/' végponton: {e}", file=sys.stderr)
            return "Hiba a főoldal betöltésekor. Részletek a szerver naplóban.", 500


    @app.route('/admin')
    def serve_admin_app():
        print("Kérés érkezett az '/admin' végpontra.", file=sys.stderr)
        try:
            print(f"Kísérlet: 'admin.html' kiszolgálása innen: {FILE_DIRECTORY}", file=sys.stderr)
            return send_from_directory(FILE_DIRECTORY, 'admin.html')
        except Exception as e:
            print(f"!!! HIBA az '/admin' végponton: {e}", file=sys.stderr)
            return "Hiba az admin oldal betöltésekor. Részletek a szerver naplóban.", 500
            
    # Egy egyszerű teszt végpont, hogy lássuk, a Flask működik-e
    @app.route('/api/test')
    def api_test():
        return jsonify({"status": "success", "message": "A Flask API működik!"})
    

