import sqlite3
import os

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database'))
db_path = os.path.join(base_dir, 'music.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Supprimer les anciennes tables si elles existent
tables = ["playlist", "association", "gout_genre", "mot_cle", "genre", "gout_utilisateur", "gout", "utilisateur"]
for table in tables:
    cursor.execute(f"DROP TABLE IF EXISTS {table}")

# Recréer proprement toutes les tables nécessaires à IAMusic
cursor.execute("""
CREATE TABLE utilisateur (
  id_utilisateur INTEGER PRIMARY KEY AUTOINCREMENT,
  nom TEXT,
  email TEXT,
  mot_de_passe TEXT,
  a_choisi_gouts INTEGER DEFAULT 0,
  access_token TEXT,
  refresh_token TEXT,
  expires_at REAL
);
""")

cursor.execute("""
CREATE TABLE gout (
  id_gout INTEGER PRIMARY KEY AUTOINCREMENT,
  nom TEXT
);
""")

cursor.execute("""
CREATE TABLE gout_utilisateur (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  id_utilisateur INTEGER,
  id_gout INTEGER,
  FOREIGN KEY (id_utilisateur) REFERENCES utilisateur(id_utilisateur),
  FOREIGN KEY (id_gout) REFERENCES gout(id_gout)
);
""")

cursor.execute("""
CREATE TABLE mot_cle (
  id_mot_cle INTEGER PRIMARY KEY AUTOINCREMENT,
  mot TEXT
);
""")

cursor.execute("""
CREATE TABLE genre (
  id_genre INTEGER PRIMARY KEY AUTOINCREMENT,
  nom_genre TEXT
);
""")

cursor.execute("""
CREATE TABLE gout_genre (
  id_gout INTEGER,
  id_genre INTEGER,
  FOREIGN KEY (id_gout) REFERENCES gout(id_gout),
  FOREIGN KEY (id_genre) REFERENCES genre(id_genre)
);
""")

cursor.execute("""
CREATE TABLE association (
  id_association INTEGER PRIMARY KEY AUTOINCREMENT,
  id_mot_cle INTEGER,
  id_genre INTEGER,
  FOREIGN KEY (id_mot_cle) REFERENCES mot_cle(id_mot_cle),
  FOREIGN KEY (id_genre) REFERENCES genre(id_genre)
);
""")

cursor.execute("""
CREATE TABLE playlist (
  id_playlist INTEGER PRIMARY KEY AUTOINCREMENT,
  uri TEXT,
  id_association INTEGER,
  FOREIGN KEY (id_association) REFERENCES association(id_association)
);
""")

conn.commit()
conn.close()
print("✅ Nouvelle base music.db créée avec succès avec toutes les tables.")
