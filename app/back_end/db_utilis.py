import os
import sqlite3

def get_db_connection():
    """Fonction utilitaire pour se connecter à la base de données"""
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database'))
        db_path = os.path.join(base_dir, 'music.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Erreur de connexion à la base de données : {e}")
        return None