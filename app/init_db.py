import sqlite3

conn = sqlite3.connect("music.db")
cursor = conn.cursor()
# Récupère l'id du mot "stress"
cursor.execute("SELECT id_mot_cle FROM mot_cle WHERE mot = ?", ("stress",))
id_stress = cursor.fetchone()[0]

# Récupère l'id du genre "chill"
cursor.execute("SELECT id_genre FROM genre WHERE nom_genre = ?", ("chill",))
id_chill = cursor.fetchone()[0]

# Récupère l'id_association correspondant
cursor.execute(
    "SELECT id_association FROM association WHERE id_mot_cle = ? AND id_genre = ?",
    (id_stress, id_chill)
)
id_association = cursor.fetchone()[0]
# Exemple de playlists Spotify associées à "stress + chill"
playlists = [
    (id_association, "spotify:playlist:0blvE99Ov7R5SZc9GY3NM2"),
    (id_association, "spotify:playlist:6UDAaJGCtNUDIHCj1yPL5Y")
]

cursor.executemany(
    "INSERT INTO playlist (id_association, uri) VALUES (?, ?)",
    playlists
)
conn.commit()
conn.close()
print("Playlists ajoutées avec succès.")