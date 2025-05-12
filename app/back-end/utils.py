import os
import spotipy
from flask import session, redirect, url_for
from spotipy.oauth2 import SpotifyOAuth

# Configuration SpotifyOAuth globale
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:5000/callback"),
    scope = "user-read-playback-state user-modify-playback-state user-read-private"

)

def get_valid_spotify_token():
    """Vérifie et renouvelle automatiquement le token Spotify si nécessaire."""
    token_info = session.get('spotify_token_info')

    if not token_info:
        return None

    if sp_oauth.is_token_expired(token_info):
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['spotify_token_info'] = token_info  # mise à jour session
        except Exception as e:
            print("Erreur lors du rafraîchissement du token Spotify:", e)
            return None

    return token_info['access_token']

def get_spotify_profile():
    """Renvoie le profil Spotify du token actif (ou None si invalide)"""
    access_token = get_valid_spotify_token()
    if not access_token:
        return None

    sp = spotipy.Spotify(auth=access_token)
    try:
        profile = sp.current_user()
        return profile
    except Exception as e:
        print("❌ Impossible de récupérer le profil Spotify :", e)
        return None

