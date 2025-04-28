import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Initialisation de l'objet Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="http://localhost:8888/callback",
    scope="user-library-read user-read-playback-state user-modify-playback-state streaming"
))

# Fonction pour obtenir un appareil actif
def obtenir_appareil_actif():
    devices = sp.devices()
    if not devices['devices']:
        print("❌ Aucun appareil actif trouvé. Ouvre Spotify sur ton téléphone ou PC.")
        return None
    return devices['devices'][0]['id']

# Fonction pour jouer une playlist
def jouer_playlist(uri):
    if not uri:
        print("❌ URI de playlist invalide.")
        return

    device_id = obtenir_appareil_actif()
    if not device_id:
        return

    try:
        sp.transfer_playback(device_id=device_id, force=True)
        sp.start_playback(context_uri=uri)
        print(f"✅ Lecture lancée : {uri}")
    except Exception as e:
        print(f"⚠️ Erreur lors de la lecture : {e}")
