import sqlite3
import os

def get_db_connection():
    db_path = "/home/callacos/IAMusic./app/database/music.db"
    return sqlite3.connect(db_path)

def get_playlist_from_phrase(user_id, phrase):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Extraire les mots de la phrase
    mots = phrase.lower().split()
    format_mots = ",".join("?" for _ in mots)
    cursor.execute(f"SELECT id_mot_cle FROM mot_cle WHERE mot IN ({format_mots})", mots)
    mots_ids = [row[0] for row in cursor.fetchall()]
    if not mots_ids:
        print("Aucun mot-clé trouvé.")
        conn.close()
        return ["spotify:playlist:37i9dQZF1DWVuV87wUBNwc"]

    # Récupérer les genres aimés par l'utilisateur
    cursor.execute("""
        SELECT gg.id_genre
        FROM gout_utilisateur gu
        JOIN gout_genre gg ON gu.id_gout = gg.id_gout
        WHERE gu.id_utilisateur = ?
    """, (user_id,))
    genres_ids = [row[0] for row in cursor.fetchall()]
    if not genres_ids:
        print("L'utilisateur n'a aucun goût enregistré.")
        conn.close()
        return

    # Récupérer les playlists qui correspondent aux mots-clés ET aux genres
    format_mots = ",".join("?" for _ in mots_ids)
    format_genres = ",".join("?" for _ in genres_ids)
    cursor.execute(f"""
    SELECT p.uri
    FROM playlist p
    JOIN association a ON p.id_association = a.id_association
    WHERE a.id_mot_cle IN ({format_mots})
    AND a.id_genre IN ({format_genres})
    ORDER BY RANDOM()
    LIMIT 1
    """, (*mots_ids, *genres_ids))

    result = cursor.fetchone()

    if result:
        print("🎶 Playlist recommandée :", result[0])
        conn.close()
        return [result[0]]
    else:
        print("😢 Aucune playlist trouvée.")
        conn.close()
        return []
