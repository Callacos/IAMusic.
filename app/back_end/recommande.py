import sqlite3
import os
from db_utilis import get_db_connection

def get_db_connection():
    db_path = "/home/callacos/IAMusic./app/database/music.db"
    return sqlite3.connect(db_path)

def get_playlist_from_phrase(user_id, phrase):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Extraire les mots de la phrase
        mots = phrase.lower().split()
        format_mots = ",".join("?" for _ in mots)
        cursor.execute(f"SELECT id_mot_cle FROM mot_cle WHERE mot IN ({format_mots})", mots)
        mots_ids = [row[0] for row in cursor.fetchall()]
        if not mots_ids:
            print("Aucun mot-clé trouvé.")
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
            return ["spotify:playlist:37i9dQZF1DWVuV87wUBNwc"]

        # Requête finale
        format_mots = ",".join("?" for _ in mots_ids)
        format_genres = ",".join("?" for _ in genres_ids)
        query = f"""
            SELECT p.uri
            FROM playlist p
            JOIN association a ON p.id_association = a.id_association
            WHERE a.id_mot_cle IN ({format_mots})
            AND a.id_genre IN ({format_genres})
            ORDER BY RANDOM()
            LIMIT 1
        """
        print("🔍 Requête avec id_mot_cle :", mots_ids)
        print("🔍 Requête avec id_genre :", genres_ids)

        cursor.execute(query, (*mots_ids, *genres_ids))
        result = cursor.fetchone()

        if result:
            print("🎶 Playlist recommandée :", result[0])
            return [result[0]]
        else:
            print("😢 Aucune playlist trouvée.")
            return ["spotify:playlist:5gcRNWl6qZOW5Zevr9y2e6"]

    except sqlite3.Error as e:
        print(f"❌ Erreur SQLite : {e}")
        return ["spotify:playlist:5gcRNWl6qZOW5Zevr9y2e6"]

    finally:
        if conn:
            conn.close()

def get_enhanced_playlist_from_phrase(user_id, phrase):
    # Récupérer les recommandations de base
    base_recommendations = get_playlist_from_phrase(user_id, phrase)
    
    # Analyser l'historique pour affiner les recommandations
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Récupérer les playlists les plus écoutées
        cursor.execute("""
            SELECT playlist_uri, COUNT(*) as count 
            FROM historique_ecoute 
            WHERE id_utilisateur = ? 
            GROUP BY playlist_uri 
            ORDER BY count DESC 
            LIMIT 5
        """, (user_id,))
        favorite_playlists = cursor.fetchall()
        
        # Analyser les interactions positives
        cursor.execute("""
            SELECT playlist_uri, COUNT(*) as interactions
            FROM interactions
            WHERE id_utilisateur = ? AND type_interaction != 'skip'
            GROUP BY playlist_uri
            ORDER BY interactions DESC
            LIMIT 5
        """, (user_id,))
        positive_interactions = cursor.fetchall()
        
        # Si aucune recommandation de base, utiliser les favorites directement
        if not base_recommendations and (favorite_playlists or positive_interactions):
            # Combiner les playlists favorites et interactions positives
            combined_playlists = {}
            
            # Ajouter poids des playlists écoutées
            for uri, count in favorite_playlists:
                combined_playlists[uri] = count
            
            # Ajouter poids des interactions positives (avec plus de valeur)
            for uri, count in positive_interactions:
                if uri in combined_playlists:
                    combined_playlists[uri] += count * 1.5  # Bonus pour interactions positives
                else:
                    combined_playlists[uri] = count * 1.5
            
            # Trier par score et prendre les 3 meilleures
            sorted_playlists = sorted(combined_playlists.items(), key=lambda x: x[1], reverse=True)
            return [uri for uri, _ in sorted_playlists[:3]]
        
        # Si des recommandations existent, prioritiser celles que l'utilisateur aime
        elif base_recommendations:
            # Créer un dictionnaire des URIs recommandées avec un score initial
            enhanced_recommendations = {uri: 1 for uri in base_recommendations}
            
            # Augmenter le score des playlists écoutées précédemment
            for uri, count in favorite_playlists:
                if uri in enhanced_recommendations:
                    enhanced_recommendations[uri] += count * 0.5
            
            # Augmenter davantage le score pour les interactions positives
            for uri, count in positive_interactions:
                if uri in enhanced_recommendations:
                    enhanced_recommendations[uri] += count * 1.0
            
            # Trier les recommandations par score et conserver l'ordre
            sorted_recommendations = sorted(
                enhanced_recommendations.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Retourner les URIs ordonnées
            return [uri for uri, _ in sorted_recommendations]
        
    except Exception as e:
        print(f"❌ Erreur lors de l'amélioration des recommandations: {e}")
    finally:
        conn.close()
    
    # En cas d'erreur ou si aucune amélioration n'est possible, retourner les recommandations originales
    return base_recommendations
