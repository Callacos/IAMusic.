import sqlite3
import os

def extraire_mots_cles(phrase):
    """Extrait les mots clés pertinents d'une phrase."""
    mots = phrase.lower().split()
    mots_filtres = [mot for mot in mots if len(mot) > 3]
    return mots_filtres if mots_filtres else mots[:2]  # Garantit au moins 1-2 mots


def trouver_playlists_depuis_phrase(phrase):
    """Trouve des playlists adaptées à une phrase donnée."""
    mots_cles = extraire_mots_cles(phrase)

    # Chemin vers la base de données
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "music.db")

    print(f"Recherche de playlists pour les mots-clés: {', '.join(mots_cles)}")
    print(f"Utilisation de la base de données: {db_path}")

    # Vérification que la base existe
    if not os.path.exists(db_path):
        print(f"❌ Erreur: La base de données n'existe pas à l'emplacement: {db_path}")
        return ["spotify:playlist:5gcRNWl6qZOW5Zevr9y2e6"]

    uris = []

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Liste temporaire des genres que l'utilisateur aime (à remplacer plus tard)
        genres_utilisateur = [1, 2, 3]  # Chill, Motivant, Relax
        mot_cle_valide_trouve = False

        for mot in mots_cles:
            # 1. Trouver l'id du mot-clé
            cursor.execute("SELECT id_mot_cle FROM mot_cle WHERE mot = ?", (mot,))
            result = cursor.fetchone()
            print(f"🔎 Mot '{mot}' → id_mot_cle trouvé : {result}")
            if not result:
                continue
            mot_cle_valide_trouve = True
            id_mot_cle = result[0]

            # 2. Trouver les associations liées à ce mot-clé
            cursor.execute("""
                SELECT id_association FROM association 
                WHERE id_mot_cle = ? AND id_genre IN ({})
            """.format(','.join(['?'] * len(genres_utilisateur))),
            [id_mot_cle] + genres_utilisateur)
            associations = cursor.fetchall()
            print(f"🔗 Associations trouvées pour id_mot_cle {id_mot_cle}: {associations}")
            if not associations:
                continue

            for (id_association,) in associations:
                # 3. Trouver les playlists liées à chaque association
                cursor.execute("SELECT uri FROM playlist WHERE id_association = ?", (id_association,))
                found_uris = [row[0] for row in cursor.fetchall()]
                print(f"🎧 URIs trouvées pour association {id_association} : {found_uris}")
                uris.extend(found_uris)

        # ✅ Ici après la boucle
        if not mot_cle_valide_trouve:
            print("⚠️ Aucun mot-clé reconnu dans la base.")
            return ["spotify:playlist:5gcRNWl6qZOW5Zevr9y2e6"]

    except sqlite3.Error as e:
        print(f"❌ Erreur de base de données: {e}")
        return ["spotify:playlist:5gcRNWl6qZOW5Zevr9y2e6"]

    finally:
        if conn:
            conn.close()

    if not uris:
        print("❗ Aucun résultat trouvé, playlist par défaut.")
        return ["spotify:playlist:5gcRNWl6qZOW5Zevr9y2e6"]

    return uris
