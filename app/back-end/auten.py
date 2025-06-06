from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

def get_spotify_for_user(spotify_id):
    cache_path = f".cache-{spotify_id}"
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-read-playback-state user-modify-playback-state streaming",
        cache_path=cache_path,
        open_browser=False 
    )
    return Spotify(auth_manager=auth_manager)

# Fonction pour obtenir un appareil actif
def obtenir_appareil_actif(sp):
    devices = sp.devices()
    if not devices['devices']:
        print("Aucun appareil actif trouvé.")
        return None, "Aucun appareil actif trouvé. Veuillez ouvrir Spotify sur un appareil."
    return devices['devices'][0]['id'], None

# Fonction pour jouer une playlist
def jouer_playlist(uri, sp):
    if uri is None:
        print("Impossible de jouer la playlist, URI invalide.")
        return

    print(f"Tentative de lecture de la playlist avec l'URI : {uri}")
    device_id, error = obtenir_appareil_actif(sp)
    if error:
        print(error)
        return

    try:
        sp.transfer_playback(device_id=device_id, force=True)
        sp.start_playback(context_uri=uri)
        print(f"Lecture lancée pour l'URI : {uri}")
    except Exception as e:
        print(f"Erreur lors de la lecture de la playlist : {e}")

# Fonction pour récupérer la lecture actuelle
def get_current_playback_info(sp):
    try:
        playback = sp.current_playback()
        if playback and playback.get('item'):
            return {
                "is_playing": playback['is_playing'],
                "title": playback['item']['name'],
                "artist": ", ".join([a['name'] for a in playback['item']['artists']]),
                "image": playback['item']['album']['images'][0]['url'],
                "progress_ms": playback['progress_ms'],
                "duration_ms": playback['item']['duration_ms']
            }
        else:
            return None
    except Exception as e:
        print("❌ Erreur lecture actuelle :", e)
        return None
