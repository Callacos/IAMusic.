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
    """Lance la lecture d'une playlist, d'un artiste ou d'un album sur Spotify"""
    
    # Vérifier le type d'URI
    valid_uri_types = {
        'spotify:playlist:': 'playlist',
        'spotify:artist:': 'artist', 
        'spotify:album:': 'album',
        'spotify:track:': 'track'
    }
    
    uri_type = None
    for prefix, type_name in valid_uri_types.items():
        if uri.startswith(prefix):
            uri_type = type_name
            break
    
    if not uri_type:
        print(f"❌ URI invalide pour jouer_playlist: {uri}")
        return False
    
    # Récupérer le token valide
    token = get_valid_spotify_token()
    if not token:
        print("❌ Pas de token valide pour jouer")
        return False
    
    user_id = session.get('user_id')
    if not user_id:
        print("❌ Utilisateur non connecté")
        return False
        
    # Récupérer l'instance Spotify
    sp = get_spotify_for_user(user_id)
    if not sp:
        print("❌ Impossible d'obtenir l'instance Spotify")
        return False
        
    # 1. D'abord lancer la lecture selon le type d'URI
    try:
        if uri_type == 'track':
            # Pour les pistes, utiliser uris au lieu de context_uri
            sp.start_playback(uris=[uri])
        else:
            # Pour les playlists, artistes et albums, utiliser context_uri
            sp.start_playback(context_uri=uri)
            
        print(f"✅ Lecture lancée : {uri}")
        lecture_ok = True
    except Exception as e:
        print(f"❌ Erreur lecture: {e}")
        return False
    
    # 2. Ensuite, essayer d'enregistrer dans l'historique
    try:
        # Extraire l'ID depuis l'URI
        entity_id = uri.split(':')[-1]
        
        # Tenter de récupérer les infos, selon le type d'URI
        try:
            if uri_type == "playlist":
                data = sp.playlist(entity_id)
                nom = data.get('name', 'Playlist inconnue')
            elif uri_type == "artist":
                data = sp.artist(entity_id)
                nom = data.get('name', 'Artiste inconnu')
            elif uri_type == "album":
                data = sp.album(entity_id)
                nom = data.get('name', 'Album inconnu')
            elif uri_type == "track":
                data = sp.track(entity_id)
                nom = data.get('name', 'Titre inconnu')
        except Exception as e:
            print(f"⚠️ Impossible de récupérer les détails: {e}")
            nom = f"{uri_type.capitalize()} inconnu"
        
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
                (id_utilisateur, uri, nom)
            )
            conn.commit()
            print(f"✅ Écoute enregistrée dans l'historique pour l'utilisateur {id_utilisateur}")
        conn.close()
        
        return lecture_ok
        
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement: {e}")
        return lecture_ok