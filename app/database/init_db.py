import sqlite3
import os

# Chemin vers la base
db_path = os.path.join(os.path.dirname(__file__), "music.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Vérifier si la colonne "email" existe déjà
cursor.execute("PRAGMA table_info(utilisateur);")
colonnes = [col[1] for col in cursor.fetchall()]

# Ajouter les colonnes manquantes
if "email" not in colonnes:
    cursor.execute("ALTER TABLE utilisateur ADD COLUMN email TEXT;")
if "mot_de_passe" not in colonnes:
    cursor.execute("ALTER TABLE utilisateur ADD COLUMN mot_de_passe TEXT;")
if "a_choisi_gouts" not in colonnes:
    cursor.execute("ALTER TABLE utilisateur ADD COLUMN a_choisi_gouts INTEGER DEFAULT 0;")

# Créer l’index unique sur l’email si besoin
cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_email_unique ON utilisateur(email);")

conn.commit()
conn.close()
print("✅ Table utilisateur mise à jour.")
