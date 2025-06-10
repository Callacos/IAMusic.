import os
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()  # Charge les variables depuis le .env

def get_spotify_oauth_for_user(nom_utilisateur):
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri="http://localhost:5000/callback",
        scope="user-read-playback-state user-modify-playback-state user-read-currently-playing",
        cache_path=f".cache-{nom_utilisateur}"
    )