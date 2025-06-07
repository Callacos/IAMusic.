import sqlite3
import os

# Chemin vers votre base de données existante
DB_PATH = os.path.join(os.path.dirname(__file__), "music.db")

# Connexion à la base de données
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Créer la table featured_playlists
cursor.execute('''
CREATE TABLE IF NOT EXISTS featured_playlists (
    id INTEGER PRIMARY KEY,
    uri TEXT NOT NULL,
    titre TEXT NOT NULL,
    date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Ajouter quelques playlists par défaut
default_playlists = [
    ('spotify:playlist:37i9dQZF1DX4WYpdgoIcn6', 'Chill Hits'),
    ('spotify:playlist:37i9dQZF1DXcBWIGoYBM5M', 'Today\'s Top Hits'),
    ('spotify:playlist:37i9dQZF1DX0hWmn8d5pRe', 'Deep Focus'),
    ('spotify:playlist:37i9dQZF1DX3rxVfibe1L0', 'Mood Booster')
]

# Vérifier si la table est vide avant d'ajouter les playlists par défaut
cursor.execute("SELECT COUNT(*) FROM featured_playlists")
count = cursor.fetchone()[0]

if count == 0:
    cursor.executemany(
        "INSERT INTO featured_playlists (uri, titre) VALUES (?, ?)",
        default_playlists
    )

conn.commit()
conn.close()

print("✅ Table featured_playlists créée avec succès!")