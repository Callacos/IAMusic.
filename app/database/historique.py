import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Essayez d'importer
try:
    from back_end.main import get_db_connection
    print("✅ Import réussi!")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    
    # Solution de secours: définir la fonction localement
    def get_db_connection():
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database'))
        db_path = os.path.join(base_dir, 'music.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table historique des recherches
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historique_recherche (
        id_historique INTEGER PRIMARY KEY AUTOINCREMENT,
        id_utilisateur INTEGER,
        phrase TEXT,
        date_recherche TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_utilisateur) REFERENCES utilisateur(id_utilisateur)
    )
    ''')
    
    # Table historique des playlists écoutées
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historique_ecoute (
        id_ecoute INTEGER PRIMARY KEY AUTOINCREMENT,
        id_utilisateur INTEGER,
        playlist_uri TEXT,
        playlist_nom TEXT,
        temps_ecoute INTEGER DEFAULT 0,
        date_ecoute TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        note INTEGER DEFAULT 0,
        FOREIGN KEY (id_utilisateur) REFERENCES utilisateur(id_utilisateur)
    )
    ''')
    
    # Table pour les interactions (play, pause, skip)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interactions (
        id_interaction INTEGER PRIMARY KEY AUTOINCREMENT,
        id_utilisateur INTEGER,
        playlist_uri TEXT,
        type_interaction TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_utilisateur) REFERENCES utilisateur(id_utilisateur)
    )
    ''')
    
    conn.commit()
    conn.close()
    
# Si le fichier est exécuté directement
if __name__ == "__main__":
    print("Création des tables d'historique...")
    create_tables()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Vérifier que les tables ont bien été créées
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables dans la base de données:")
    for table in tables:
        print(f"- {table[0]}")
    
    conn.close()
    print("✅ Opération terminée!")
