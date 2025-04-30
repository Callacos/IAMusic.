import sqlite3
import os

def extraire_mots_cles(phrase):
    """Extrait les mots clés pertinents d'une phrase."""
    # Version simple: diviser la phrase en mots et filtrer les mots courts
    mots = phrase.lower().split()
    # Filtrer les mots courts et les mots vides
    mots_filtres = [mot for mot in mots if len(mot) > 3]
    return mots_filtres if mots_filtres else mots[:2]  # Retourne au moins quelques mots

def trouver_playlists_depuis_phrase(phrase):
    """Trouve des playlists adaptées à une phrase donnée."""
    mots_cles = extraire_mots_cles(phrase)
    
    # Chemin correct vers la base de données
    # Remonte d'un niveau depuis back-end et va dans database
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "music.db")
    
    print(f"Recherche de playlists pour les mots-clés: {', '.join(mots_cles)}")
    print(f"Utilisation de la base de données: {db_path}")
    
    # Vérifier si la base de données existe
    if not os.path.exists(db_path):
        print(f"❌ Erreur: La base de données n'existe pas à l'emplacement: {db_path}")
        return ["spotify:playlist:5gcRNWl6qZOW5Zevr9y2e6"]  # Playlist par défaut
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Recherche des playlists correspondantes...
        # ... [Le reste de votre code de recherche reste inchangé]
        
    except sqlite3.Error as e:
        print(f"❌ Erreur de base de données: {e}")
        return ["spotify:playlist:5gcRNWl6qZOW5Zevr9y2e6"]  # Playlist par défaut
    finally:
        if conn:
            conn.close()