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
    
    # Empêcher les appels récursifs infinis
    max_attempts = 1  # Pas de récursion
    
    # Vérifier que l'URI est bien une playlist
    if not uri.startswith('spotify:playlist:'):
        print(f"❌ URI invalide pour jouer_playlist: {uri}")
        return False
    
    try:
        # Récupérer le token valide
        token = get_valid_spotify_token()
        if not token:
            print("❌ Pas de token valide pour jouer la playlist")
            return False
        
        user_id = session.get('user_id')
        if not user_id:
            print("❌ Utilisateur non connecté")
            return False
            
        # Récupérer les infos de la playlist
        sp = get_spotify_for_user(user_id)
        if not sp:
            print("❌ Impossible d'obtenir l'instance Spotify")
            return False
        
        # Bypass la vérification de l'existence de la playlist et essayer de jouer directement
        try:
            sp.start_playback(context_uri=uri)
            print(f"✅ Lecture lancée : {uri}")
            
            # Enregistrer l'écoute
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Récupérer l'ID utilisateur
                cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE nom = ?", (user_id,))
                result = cursor.fetchone()
                if result:
                    id_utilisateur = result[0]
                    cursor.execute(
                        "INSERT INTO historique_ecoute (id_utilisateur, uri_playlist, date_ecoute) VALUES (?, ?, datetime('now'))",
                        (id_utilisateur, uri)
                    )
                    conn.commit()
                    print(f"✅ Écoute enregistrée dans l'historique pour l'utilisateur {id_utilisateur}")
                conn.close()
            except Exception as e:
                print(f"❌ Erreur DB: {e}")
                
            return True
        except Exception as e:
            print(f"❌ Erreur lecture: {e}")
            # Ne PAS rappeler jouer_playlist récursivement ici
            return False
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False
