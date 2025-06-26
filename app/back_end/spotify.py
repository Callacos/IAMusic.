import spotipy
from flask import session
from utils import get_valid_spotify_token
from spotify_auth import get_spotify_oauth_for_user
from auten import get_spotify_for_user
from db_utilis import get_db_connection

# Fonction pour créer une instance Spotipy avec le bon token
def get_spotify_client():
    access_token = get_valid_spotify_token()
    if not access_token:
        print("❌ Token Spotify invalide ou expiré.")
        return None
    return spotipy.Spotify(auth=access_token)

# Fonction pour obtenir un appareil actif
def obtenir_appareil_actif(sp):
    try:
        devices = sp.devices()
        if not devices['devices']:
            print("❌ Aucun appareil actif trouvé. Ouvre Spotify sur ton téléphone ou PC.")
            return None
        return devices['devices'][0]['id']
    except Exception as e:
        print("❌ Erreur lors de l’obtention des appareils :", e)
        return None

# Fonction pour jouer une playlist
def jouer_playlist(uri):
    """Lance la lecture d'une playlist sur le compte Spotify de l'utilisateur"""
    
    # Vérifier que l'URI est bien une playlist
    if not uri.startswith('spotify:playlist:'):
        print(f"❌ URI invalide pour jouer_playlist: {uri}")
        return False
    
    # Récupérer le token valide
    token = get_valid_spotify_token()
    if not token:
        print("❌ Pas de token valide pour jouer la playlist")
        return False
    
    user_id = session.get('user_id')
    if not user_id:
        print("❌ Utilisateur non connecté")
        return False
        
    # Récupérer les infos de la playlist
    sp = get_spotify_for_user(user_id)
    if not sp:
        print("❌ Impossible d'obtenir l'instance Spotify")
        return False
        
    # 1. D'abord lancer la lecture sans vérifier l'existence
    try:
        sp.start_playback(context_uri=uri)
        print(f"✅ Lecture lancée : {uri}")
        lecture_ok = True
    except Exception as e:
        print(f"❌ Erreur lecture: {e}")
        return False
    
    # 2. Ensuite, essayer d'enregistrer dans l'historique, même si les détails ne sont pas disponibles
    try:
        # Extraire l'ID de la playlist depuis l'URI
        playlist_id = uri.split(':')[-1]
        
        # Tenter de récupérer les infos de la playlist, mais ne pas bloquer si ça échoue
        try:
            playlist_data = sp.playlist(playlist_id)
            playlist_nom = playlist_data.get('name', 'Playlist inconnue')
        except Exception as e:
            print(f"⚠️ Impossible de récupérer les détails de la playlist: {e}")
            playlist_nom = "Playlist inconnue"  # Valeur par défaut si on ne peut pas récupérer le nom
        
        # Enregistrer l'écoute dans l'historique
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupérer l'ID utilisateur
        cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE nom = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            id_utilisateur = result[0]
            
            # Enregistrer l'écoute
            cursor.execute(
                "INSERT INTO historique_ecoute (id_utilisateur, playlist_uri, playlist_nom) VALUES (?, ?, ?)",
                (id_utilisateur, uri, playlist_nom)
            )
            conn.commit()
            print(f"✅ Écoute enregistrée dans l'historique pour l'utilisateur {id_utilisateur}")
        conn.close()
        
        # La lecture a déjà été lancée, retourner vrai
        return lecture_ok
        
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement de l'écoute: {e}")
        # Même s'il y a une erreur dans l'enregistrement, la lecture a bien été lancée
        return lecture_ok