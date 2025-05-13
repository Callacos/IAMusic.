import spotipy
from flask import session
from utils import get_valid_spotify_token

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
    if not uri:
        print("❌ URI de playlist invalide.")
        return

    sp = get_spotify_client()
    if not sp:
        return

    device_id = obtenir_appareil_actif(sp)
    if not device_id:
        return

    try:
        sp.transfer_playback(device_id=device_id, force_play=True)
        sp.start_playback(context_uri=uri)
        print(f"✅ Lecture lancée : {uri}")
    except Exception as e:
        print(f"⚠️ Erreur lors de la lecture : {e}")
