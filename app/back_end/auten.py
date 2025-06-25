from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from flask import session, Flask, request, jsonify
import os
import sqlite3
import json
from flask import Blueprint
auten_bp = Blueprint("auten", __name__)


# Create Flask app
app = Flask(__name__)

# Function to create a database connection
def get_db_connection():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'music.db'))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

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
        print(f"Erreur lors du lancement de la lecture: {e}")
        return
    # Enregistrer dans l'historique
    id_utilisateur = session.get("utilisateur_id")
    if id_utilisateur:
        try:
            # Récupérer les infos de la playlist
            playlist_data = sp.playlist(uri.split(':')[-1])
            playlist_nom = playlist_data.get('name', 'Playlist inconnue')
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Récupérer l'ID utilisateur
            cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE nom = ?", (id_utilisateur,))
            result = cursor.fetchone()
            if result:
                id_utilisateur = result[0]
                
                # Enregistrer l'écoute
                cursor.execute(
                    "INSERT INTO historique_ecoute (id_utilisateur, playlist_uri, playlist_nom) VALUES (?, ?, ?)",
                    (id_utilisateur, uri, playlist_nom)
                )
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erreur lors de la lecture de la playlist : {e}")

def get_track_info(uri, sp):
    try:
        track = sp.track(uri)
        return {
            "nom": track["name"],
            "artiste": track["artists"][0]["name"],
            "image": track["album"]["images"][0]["url"],
            "uri": uri
        }
    except Exception as e:
        print(f"Erreur récupération titre : {e}")
        return {
            "nom": "Titre inconnu",
            "artiste": "Artiste inconnu",
            "image": "/static/images/default.jpg",  # une image par défaut
            "uri": uri
        }
    
@auten_bp.route('/jouer', methods=['POST'])
def jouer():
    data = request.get_json()
    uri = data.get('uri')
    if not uri:
        return jsonify({"error": "Pas d'URI"}), 400
    
    user_id = session.get("user_id") or session.get("utilisateur_id")
    if not user_id:
        return jsonify({"error": "Utilisateur non connecté"}), 401
    
    sp = get_spotify_for_user(user_id)
    device_id, error = obtenir_appareil_actif(sp)
    if error:
        return jsonify({"error": error}), 400

    try:
        sp.transfer_playback(device_id=device_id, force_play=True)
        sp.start_playback(uris=[uri])  # ← uris=[] = une track unique
        return jsonify({"status": "Lecture lancée"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



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

def get_titre_semaine_infos():
    try:
        from flask import session
        user_id = session.get("user_id") or session.get("utilisateur_id")
        if not user_id:
            return {
                "nom": "Non connecté",
                "artiste": "—",
                "image": "/static/images/default.jpg",
                "uri": ""
            }

        with open("titre_semaine.json", "r", encoding="utf-8") as f:
            titre_json = json.load(f)

        sp = get_spotify_for_user(user_id)
        return get_track_info(titre_json["uri"], sp)

    except Exception as e:
        print("❌ Erreur titre de la semaine :", e)
        return {
            "nom": "Erreur",
            "artiste": "—",
            "image": "/static/images/default.jpg",
            "uri": ""
        }

