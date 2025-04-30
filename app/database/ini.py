import sqlite3

conn = sqlite3.connect('music.db')
cursor = conn.cursor()

def creer_tables_utilisateurs_et_gouts():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gout (
        id_gout INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT UNIQUE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utilisateur (
        id_utilisateur INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utilisateur_gout (
        id_utilisateur INTEGER,
        id_gout INTEGER,
        PRIMARY KEY (id_utilisateur, id_gout),
    conn.commit()

creer_tables_utilisateurs_et_gouts()
print("Tables créées avec succès.")ENCES gout(id_gout)
    );
    """)

    conn.commit()
print("Tables créées avec succès.")