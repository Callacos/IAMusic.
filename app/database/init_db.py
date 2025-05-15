import sqlite3
import os

# Chemin vers la base
db_path = os.path.join(os.path.dirname(__file__), "music.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Vérifier si la colonne "email" existe déjà
cursor.execute("PRAGMA table_info(utilisateur);")
colonnes = [col[1] for col in cursor.fetchall()]

# ✅ Ajout des colonnes pour Spotify
if "access_token" not in colonnes:
    cursor.execute("ALTER TABLE utilisateur ADD COLUMN access_token TEXT;")
if "refresh_token" not in colonnes:
    cursor.execute("ALTER TABLE utilisateur ADD COLUMN refresh_token TEXT;")
if "expires_at" not in colonnes:
    cursor.execute("ALTER TABLE utilisateur ADD COLUMN expires_at REAL;")



conn.commit()
conn.close()
print("✅ Table utilisateur mise à jour.")
