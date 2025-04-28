import sqlite3

# Connexion à la base
conn = sqlite3.connect("music.db")
cursor = conn.cursor()

# Créer les tables si elles n'existent pas
cursor.execute('''
CREATE TABLE IF NOT EXISTS gout (
    id_gout INTEGER PRIMARY KEY,
    nom TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS utilisateur (
    id_utilisateur INTEGER PRIMARY KEY,
    nom TEXT NOT NULL
)
''')

# Remplir la table gout
gouts = [
    (1, "rock"),
    (2, "jazz"),
    (3, "chill"),
    (4, "var_fr"),
    (5, "tendance"),
    (6, "électro"),
    (7, "pop"),
    (8, "rap"),
    (9, "classique"),
    (10, "metal")
]

cursor.executemany("INSERT OR IGNORE INTO gout (id_gout, nom) VALUES (?, ?)", gouts)

# Remplir la table utilisateur
utilisateurs = [
    (1, "Alice"),
    (2, "Bob"),
    (3, "Charlie")
]

cursor.executemany("INSERT OR IGNORE INTO utilisateur (id_utilisateur, nom) VALUES (?, ?)", utilisateurs)

# Sauvegarder et fermer
conn.commit()
conn.close()

print("Base de données initialisée avec succès!")