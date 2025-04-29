import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('music.db')
cursor = conn.cursor()

# Exemple d'association entre id_association et id_gout_utilisateur
# ➔ Ici tu dois mettre les bonnes correspondances que tu veux toi
remplissage = {
    1: 3,  # id_association 1 → id_gout_utilisateur 3
    2: 5,  # id_association 2 → id_gout_utilisateur 5
    3: 2,  # id_association 3 → id_gout_utilisateur 2
    4: 7   # id_association 4 → id_gout_utilisateur 7
}

# Parcours du dictionnaire et mise à jour de chaque ligne
for id_association, id_gout_utilisateur in remplissage.items():
    cursor.execute(
        "UPDATE association SET id_gout_utilisateur = ? WHERE id_association = ?",
        (id_gout_utilisateur, id_association)
    )

# Sauvegarde des changements
conn.commit()

# Fermeture de la connexion
conn.close()

print("Mise à jour terminée avec succès ✅")
