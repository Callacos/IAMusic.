import os
import spotipy
from flask import session, redirect, url_for
from spotipy.oauth2 import SpotifyOAuth
import sqlite3
import time
from spotify_auth  import get_spotify_oauth_for_user 

# Configuration SpotifyOAuth globale
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:5000/callback"),
    scope = "user-read-playback-state user-modify-playback-state user-read-private"

)

def get_valid_spotify_token():
    print("📡 Appel de get_valid_spotify_token")
    nom = session.get('user_id')
    print("👤 Session user_id =", nom)

    if not nom:
        print("⚠️ Aucun utilisateur en session pour get_valid_spotify_token")
        return None

    return get_valid_token_from_db(nom)

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
    
def get_spotify_oauth_for_user(nom_utilisateur):
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri="http://127.0.0.1:5000/callback",
        scope="user-read-playback-state user-modify-playback-state streaming user-read-private",
        cache_path=f".cache-{nom_utilisateur}",
        show_dialog=True
    )

def save_spotify_tokens(nom_utilisateur, token_info):
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "music.db"))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    access_token = token_info['access_token']
    refresh_token = token_info.get('refresh_token')
    expires_at = token_info['expires_at']

    if refresh_token:
        cursor.execute("""
            UPDATE utilisateur 
            SET access_token = ?, refresh_token = ?, expires_at = ? 
            WHERE nom = ?;
        """, (access_token, refresh_token, expires_at, nom_utilisateur))
    else:
        cursor.execute("""
            UPDATE utilisateur 
            SET access_token = ?, expires_at = ? 
            WHERE nom = ?;
        """, (access_token, expires_at, nom_utilisateur))

    conn.commit()
    conn.close()

"""def get_valid_token_from_db(nom_utilisateur):
    db_path = os.path.join(os.path.dirname(__file__), "music.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT access_token, refresh_token, expires_at FROM utilisateur WHERE nom = ?", (nom_utilisateur,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    access_token, refresh_token, expires_at = row
    sp_oauth = get_spotify_oauth_for_user(nom_utilisateur)

    print("📥 Tokens en base :", access_token, refresh_token, expires_at)
    print("⏱️ Timestamp actuel :", time.time())

    if expires_at and float(expires_at) > time.time():
        return access_token

    # Token expiré, on le refresh
    try:
        new_token_info = sp_oauth.refresh_access_token(refresh_token)
        save_spotify_tokens(nom_utilisateur, new_token_info)
        return new_token_info['access_token']

    except Exception as e:
        print("❌ Exception levée :", e)
        return None"""

def get_valid_token_from_db(nom_utilisateur):
    import time
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "music.db"))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT access_token, refresh_token, expires_at FROM utilisateur WHERE nom = ?", (nom_utilisateur,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("❌ Aucun utilisateur trouvé :", nom_utilisateur)
        return None

    access_token, refresh_token, expires_at = row
    sp_oauth = get_spotify_oauth_for_user(nom_utilisateur)

    print("📥 TOKENS EN BASE")
    print("  access_token :", access_token)
    print("  refresh_token :", refresh_token)
    print("  expires_at :", expires_at)
    print("  now :", time.time())

    if expires_at and float(expires_at) > time.time():
        print("✅ Token encore valide")
        return access_token

    try:
        print("🔄 Tentative de refresh du token expiré...")
        new_token_info = sp_oauth.refresh_access_token(refresh_token)
        save_spotify_tokens(nom_utilisateur, new_token_info)
        print("✅ Nouveau token obtenu :", new_token_info['access_token'])
        return new_token_info['access_token']

    except Exception as e:
        print("❌ Erreur pendant le refresh :", e)
        return None


    

def get_spotify_client():
    nom = session.get('user_id')
    if not nom:
        return None

    access_token = get_valid_token_from_db(nom)
    if not access_token:
        return None

    return spotipy.Spotify(auth=access_token)
