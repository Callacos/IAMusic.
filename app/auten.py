from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

# Configuration pour l'authentification avec les scopes nécessaires
sp = Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="http://localhost:8888/callback",
    scope="user-library-read user-read-playback-state user-modify-playback-state streaming"
))
print("Connexion à Spotify réussie")

# Fonction pour obtenir un appareil actif
def obtenir_appareil_actif(sp):
    devices = sp.devices()
    if not devices['devices']:
        print("Aucun appareil actif trouvé.")
        return None, "Aucun appareil actif trouvé. Veuillez ouvrir Spotify sur un appareil."
    
    # Retourne l'ID du premier appareil actif
    return devices['devices'][0]['id'], None

# Fonction pour jouer une playlist
def jouer_playlist(uri):
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

# Exemple d'utilisation pour tester la fonction
if __name__ == "__main__":
    playlist_uri = 'spotify:playlist:EXEMPLE_DE_PLAYLIST_URI'
    jouer_playlist(playlist_uri)
