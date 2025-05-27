import sqlite3
import os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "music.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Genres
cursor.executemany("INSERT INTO genre (nom_genre) VALUES (?)", [
    ('rock',), ('jazz',), ('lofi',)
])

# Goûts
cursor.executemany("INSERT INTO gout (nom) VALUES (?)", [
    ('calme',), ('motivation',)
])

# Lien goût ↔ genre
cursor.executemany("INSERT INTO gout_genre (id_gout, id_genre) VALUES (?, ?)", [
    (1, 2),  # calme → jazz
    (2, 1)   # motivation → rock
])

# Mots-clés
cursor.executemany("INSERT INTO mot_cle (mot) VALUES (?)", [
    ('stress',), ('travail',)
])

# Associations mot + genre
cursor.executemany("INSERT INTO association (id_mot_cle, id_genre) VALUES (?, ?)", [
    (1, 1),  # stress + rock
    (1, 2),  # stress + jazz
    (2, 3)   # travail + lofi
])

# Playlists
cursor.executemany("INSERT INTO playlist (uri, id_association) VALUES (?, ?)", [
    ('https://open.spotify.com/playlist/rock_stress', 1),
    ('https://open.spotify.com/playlist/jazz_stress', 2),
    ('https://open.spotify.com/playlist/lofi_travail', 3)
])

conn.commit()
conn.close()
print("✅ Données de test insérées dans music.db.")
