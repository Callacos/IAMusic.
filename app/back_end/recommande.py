import sqlite3
import os
from flask import session
from db_utilis import get_db_connection
from text_analyzer import extract_keywords_with_ollama
from text_analyzer import normalize_keywords
from config import USE_IA 
from recommande import normalize_keywords 
from nltk.stem import WordNetLemmatizer

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Dictionary mapping of synonyms
synonym_map = {
    # Example entries (replace with your actual synonyms)
    'happy': 'joyeux',
    'sad': 'triste',
    'angry': 'en colère',
    'relaxed': 'relax'
    # Add more synonyms as needed
}

# Fonction d'extraction de mots-clés traditionnelle (votre méthode actuelle)
def extract_keywords_traditional(phrase):
    """Extraits des mots-clés d'une phrase en utilisant la base de données et les synonymes"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Vérifier d'abord dans la map de synonymes
        phrase_lower = phrase.lower()
        
        # Nouvelle étape: vérifier les variations par lemmatisation
        try:
            lemmatized_phrase = lemmatizer.lemmatize(phrase_lower, pos='v')
            if lemmatized_phrase != phrase_lower:
                print(f"🔄 Phrase lemmatisée: '{phrase_lower}' → '{lemmatized_phrase}'")
                # Vérifier si la version lemmatisée est dans les synonymes
                if lemmatized_phrase in synonym_map:
                    return [synonym_map[lemmatized_phrase]]
        except:
            pass
            
        # Vérifier la phrase directement dans les synonymes
        if phrase_lower in synonym_map:
            print(f"🔍 Synonyme trouvé: '{phrase_lower}' → '{synonym_map[phrase_lower]}'")
            return [synonym_map[phrase_lower]]
            
        # Récupérer tous les mots-clés de la base de données
        cursor.execute("SELECT mot FROM mot_cle")
        all_keywords = [row[0].lower() for row in cursor.fetchall()]

        # Chercher les expressions entières d'abord
        found_keywords = []
        for keyword in all_keywords:
            if keyword in phrase_lower:
                found_keywords.append(keyword)

        # Supprimer les doublons imbriqués
        filtered_keywords = []
        for kw in sorted(found_keywords, key=len, reverse=True):
            if not any(kw in longer_kw and kw != longer_kw for longer_kw in filtered_keywords):
                filtered_keywords.append(kw)

        # Si aucun mot-clé trouvé, générer des mots-clés aléatoires
        if not filtered_keywords:
            print("ℹ️ Aucun mot-clé trouvé, sélection aléatoire")
            cursor.execute("SELECT mot FROM mot_cle ORDER BY RANDOM() LIMIT 3")
            random_keywords = [row[0].lower() for row in cursor.fetchall()]
            if random_keywords:
                print(f"🎲 Mots-clés aléatoires: {random_keywords}")
                return random_keywords
            else:
                return ['relax', 'moderne', 'populaire']  # Fallback si la BD est vide
                
        return filtered_keywords

    except Exception as e:
        print(f"Erreur lors de l'extraction des mots-clés: {e}")
        return ['relax', 'moderne', 'populaire']  # Mots-clés par défaut

    finally:
        conn.close()

# Fonction unifiée d'extraction de mots-clés
from text_analyzer import extract_keywords_with_ollama
from db_utilis import get_db_connection

def extract_keywords(phrase):
    """
    Extrait les mots-clés d'une phrase utilisateur.
    Utilise Ollama si l'IA est activée, sinon méthode traditionnelle.
    Applique une normalisation et filtre par les mots-clés présents en BDD.
    """
    print(f"🔍 Analyse de la phrase : '{phrase}'")

    use_ia = session.get('use_ia', True)
    keywords = None

    if use_ia:
        try:
            keywords = extract_keywords_with_ollama(phrase)
            print(f"🤖 Mots-clés extraits par IA: {keywords}")
        except Exception as e:
            print(f"⚠️ Erreur IA : {e}")
            keywords = None

    if not keywords:
        print("📚 Utilisation de la méthode traditionnelle")
        return extract_keywords_traditional(phrase)

    # Normalisation
    keywords = normalize_keywords(keywords)

    # Vérification en base
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mot FROM mot_cle")
    mots_de_la_db = [row[0].lower() for row in cursor.fetchall()]
    conn.close()

    found = [k for k in keywords if k in mots_de_la_db]
    not_found = [k for k in keywords if k not in mots_de_la_db]

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
def get_enhanced_playlist_from_phrase(user_id, phrase, extracted_keywords=None):
    """Récupère des playlists en fonction d'une phrase utilisateur"""
    
    # Extraction des mots-clés si non fournis
    keywords = extracted_keywords if extracted_keywords else extract_keywords(phrase)
    print(f"🔑 Mots-clés extraits : {keywords}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Récupérer les ID des mots-clés
        placeholders = ','.join(['?'] * len(keywords))
        cursor.execute(f"SELECT id_mot_cle FROM mot_cle WHERE mot IN ({placeholders})", keywords)
        keyword_ids = [row[0] for row in cursor.fetchall()]
        print(f"🔍 Requête avec id_mot_cle : {keyword_ids}")
        
        # Si aucun mot-clé trouvé, utiliser un mot-clé aléatoire
        if not keyword_ids:
            cursor.execute("SELECT id_mot_cle FROM mot_cle ORDER BY RANDOM() LIMIT 1")
            result = cursor.fetchone()
            if result:
                keyword_ids = [result[0]]
            else:
                print("⚠️ Aucun mot-clé trouvé dans la base de données")
                # Utiliser une playlist par défaut connue
                return ["spotify:playlist:37i9dQZEVXbMDoHDwVN2tF"]  # Top 50 Global
        
        # VERSION SIMPLIFIÉE: Trouver une playlist qui correspond à au moins un des mots-clés
        query = """
        SELECT DISTINCT p.uri 
        FROM playlist p
        JOIN playlist_mot_cle pmk ON p.id_playlist = pmk.id_playlist
        WHERE pmk.id_mot_cle IN ({0})
        ORDER BY RANDOM()
        LIMIT 1
        """.format(','.join(['?'] * len(keyword_ids)))
        
        cursor.execute(query, keyword_ids)
        result = cursor.fetchone()
        
        if result:
            print(f"🎶 Playlist recommandée : {result[0]}")
            return [result[0]]
        else:
            # Aucune playlist trouvée avec ces mots-clés, prendre une playlist aléatoire
            cursor.execute("SELECT uri FROM playlist ORDER BY RANDOM() LIMIT 1")
            result = cursor.fetchone()
            if result:
                print(f"🎲 Playlist aléatoire : {result[0]}")
                return [result[0]]
            else:
                # Aucune playlist dans la base, utiliser une playlist par défaut connue
                return ["spotify:playlist:37i9dQZEVXbMDoHDwVN2tF"]  # Top 50 Global
    
    except Exception as e:
        print(f"❌ Erreur recommendation: {e}")
        # En cas d'erreur, retourner une playlist par défaut connue
        return ["spotify:playlist:37i9dQZEVXbMDoHDwVN2tF"]  # Top 50 Global
        
    finally:
        conn.close()