import sqlite3
import os
from db_utilis import get_db_connection
from text_analyzer import extract_keywords_with_ollama

# Fonction d'extraction de mots-clés traditionnelle (votre méthode actuelle)
def extract_keywords_traditional(phrase):
    """
    Extrait les mots-clés d'une phrase en recherchant dans la base de données des mots-clés
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Récupérer tous les mots-clés de la base de données
        cursor.execute("SELECT mot FROM mot_cle")
        all_keywords = [row[0].lower() for row in cursor.fetchall()]
        
        # Convertir la phrase en minuscules pour la comparaison
        phrase_lower = phrase.lower()
        
        # Chercher chaque mot-clé dans la phrase
        found_keywords = []
        for keyword in all_keywords:
            if keyword in phrase_lower:
                found_keywords.append(keyword)
        
        print(f"Mots-clés trouvés dans la BD: {found_keywords}")
        
        # Si aucun mot-clé trouvé, utiliser des valeurs par défaut qui existent dans la BD
        if not found_keywords:
            cursor.execute("SELECT mot FROM mot_cle ORDER BY RANDOM() LIMIT 3")
            default_keywords = [row[0] for row in cursor.fetchall()]
            print(f"Utilisation de mots-clés par défaut: {default_keywords}")
            return default_keywords
        
        return found_keywords[:3]  # Limiter à 3 mots-clés
        
    except Exception as e:
        print(f"Erreur lors de l'extraction des mots-clés: {e}")
        return ['relax', 'moderne', 'populaire']  # Fallback absolu
    finally:
        conn.close()

# Fonction unifiée d'extraction de mots-clés
from text_analyzer import extract_keywords_with_ollama
from db_utilis import get_db_connection

def extract_keywords(phrase):
    """
    Fonction qui extrait les mots-clés d'une phrase utilisateur.
    Utilise Ollama en priorité, puis une méthode traditionnelle si nécessaire.
    Inclut normalisation et filtre sur les mots-clés disponibles en BDD.
    """
    print(f"🔍 Analyse de la phrase : '{phrase}'")

    # Étape 1 : extraire les mots-clés via IA
    try:
        keywords = extract_keywords_with_ollama(phrase)
    except Exception as e:
        print(f"⚠️ Erreur lors de l'utilisation d'Ollama: {e}")
        keywords = None

    if not keywords or len(keywords) == 0:
        print("📚 Utilisation de la méthode traditionnelle")
        return extract_keywords_traditional(phrase)

    print(f"🤖 Mots-clés extraits par IA: {keywords}")

    # Étape 2 : normalisation
    synonym_map = {
        "bouger": "bouge",
        "bougé": "bouge",
        "je veux bouge": "bouge",
        "danser": "bouge",
        "dance": "bouge",
        "rhythmic": "bouge",
        "calm": "relax",
        "chill": "relax",
        "peace": "relax",
        "relaxing": "relax",
        "tense": "stress",
        "anxious": "stress",
        "energetic": "énergie",
        "motivation": "énergie",
        "stressé": "stress"
    }

    normalized_keywords = [synonym_map.get(k, k) for k in keywords]

    # Étape 3 : comparaison avec la BDD
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mot FROM mot_cle")
    mots_de_la_db = [row[0].lower() for row in cursor.fetchall()]
    conn.close()

    found = [k for k in normalized_keywords if k in mots_de_la_db]
    not_found = [k for k in normalized_keywords if k not in mots_de_la_db]

    print(f"✅ Mots reconnus en BDD : {found}")
    print(f"❌ Mots ignorés (non trouvés en BDD) : {not_found}")

    return found[:3] if found else extract_keywords_traditional(phrase)


# Mise à jour de la fonction get_playlist_from_phrase pour utiliser les mots-clés
def get_playlist_from_phrase(user_id, phrase, keywords=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Si aucun mot-clé n'est fourni, les extraire de la phrase
        if keywords is None:
            keywords = extract_keywords(phrase)
            print(f"🔑 Mots-clés extraits : {keywords}")
        
        # Extraire les IDs des mots-clés
        format_mots = ",".join("?" for _ in keywords)
        cursor.execute(f"SELECT id_mot_cle FROM mot_cle WHERE mot IN ({format_mots})", keywords)
        mots_ids = [row[0] for row in cursor.fetchall()]
        
        if not mots_ids:
            print("⚠️ Aucun mot-clé trouvé dans la base de données.")
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
            print("ℹ️ L'utilisateur n'a aucun goût enregistré.")
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

# Mise à jour de get_enhanced_playlist_from_phrase pour accepter des mots-clés
def get_enhanced_playlist_from_phrase(user_id, phrase, keywords=None):
    # Récupérer les recommandations de base avec les mots-clés (si fournis)
    base_recommendations = get_playlist_from_phrase(user_id, phrase, keywords)
    
    # Le reste de la fonction reste inchangé
    # ...
    
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