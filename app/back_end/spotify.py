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
        # Si c'est un artiste, convertir en URI de playlist de l'artiste
        if uri.startswith('spotify:artist:'):
            artist_id = uri.split(':')[-1]
            print(f"🔄 Conversion de l'URI artiste en playlist This Is...")
            # Utiliser une playlist "This Is..." pour cet artiste
            return jouer_playlist(f"spotify:playlist:37i9dQZF1DXcBWIGoYBM5M")  # Playlist par défaut
        return False
    
    try:
        # Récupérer le token valide
        token = get_valid_spotify_token()
        if not token:
            print("❌ Pas de token valide pour jouer la playlist")
            return False
            
        # Ce bloc doit être indenté correctement (au même niveau que le try ci-dessus)
        user_id = session.get('user_id')
        if user_id:
            try:
                # Récupérer les infos de la playlist
                sp = get_spotify_for_user(user_id)
                if sp:
                    playlist_data = sp.playlist(uri.split(':')[-1])
                    playlist_nom = playlist_data.get('name', 'Playlist inconnue')
                    
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
            except Exception as e:
                print(f"❌ Erreur lors de l'enregistrement de l'écoute: {e}")
                return False
    except Exception as e:
        print(f"❌ Erreur lors de la lecture de la playlist: {e}")
        return False
