from flask import Flask, request, send_from_directory, render_template_string
from flask import render_template
from flask import session, redirect, url_for
from flask import redirect, url_for, session, flash
from ia import trouver_playlists_depuis_phrase
from spotify import jouer_playlist
import spotipy
import os
import sqlite3
import time
import requests
import json
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from utils import get_valid_spotify_token, sp_oauth, get_spotify_profile
import spotipy
from utils import get_valid_spotify_token
from utils import get_spotify_oauth_for_user
from recommande import get_playlist_from_phrase
from auten import get_current_playback_info
from auten import get_spotify_for_user
from flask import jsonify

def get_valid_spotify_token():
    nom_utilisateur = session.get('user_id')
    if not nom_utilisateur:
        print("❌ Aucun utilisateur en session.")
        return None

    sp_oauth = get_spotify_oauth_for_user(nom_utilisateur)
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        print("❌ Aucun token trouvé pour", nom_utilisateur)
        return None

    if sp_oauth.is_token_expired(token_info):
        print("🔁 Token expiré, tentative de rafraîchissement...")
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info['access_token']

def get_db_connection():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database'))
    db_path = os.path.join(base_dir, 'music.db')
    return sqlite3.connect(db_path)

app = Flask(
    __name__,
    template_folder='../templates',
    static_folder='../static'
)
app.secret_key = 'une_clé_secrète_pour_la_session'


# Route HTML principale
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 1) On lit a_choisi_gouts depuis la table utilisateur
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT a_choisi_gouts FROM utilisateur WHERE nom = ?", (session['user_id'],))
    row = cursor.fetchone()
    conn.close()

    # 2) S’il n’a pas encore coché ses goûts (valeur 0), on redirige vers /preferences
    if not row or row[0] == 0:
        return redirect(url_for('preferences'))

    # 3) Sinon, on affiche l’accueil “normal” :
    display_name = session.get('spotify_display_name', 'Utilisateur')
    player_info = None
    try:
        sp_local = get_spotify_for_user(session['user_id'])
        playback = sp_local.current_playback()
        if playback and playback.get('item'):
            item = playback['item']
            player_info = {
                'titre': item['name'],
                'artiste': item['artists'][0]['name'],
                'image': item['album']['images'][0]['url'],
                'is_playing': playback['is_playing']
            }
    except Exception as e:
        print("⚠️ Impossible de récupérer le playback :", e)

    # Charger l’artiste de la semaine
    artiste = None
    artiste_path = os.path.join(os.path.dirname(__file__), "artiste_semaine.json")
    try:
        with open(artiste_path, "r") as f:
            artiste = json.load(f)
    except:
        pass

    token = get_valid_spotify_token()
    if not token:
        return "❌ Erreur d'authentification Spotify", 403

    return render_template(
        "index.html",
        display_name=display_name,
        artiste=artiste,
        player_info=player_info,
        spotify_token=token
    )





# Route pour le fichier CSS
@app.route('/style.css')
def style():
    return send_from_directory('../front-end', 'style.css')

# Route qui reçoit la phrase du front-end
@app.route('/phrase', methods=['POST'])
def recevoir_phrase():
    data = request.get_json()
    phrase = data.get('phrase')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE nom = ?", (session["user_id"],))
    utilisateur = cursor.fetchone()
    conn.close()

    if utilisateur:
        user_id = utilisateur[0]
        uris = get_playlist_from_phrase(user_id, phrase)
    else:
        return "❌ Utilisateur non trouvé"


    if uris:
        jouer_playlist(uris[0])  # Lecture automatique si URI trouvée
        url = f"https://open.spotify.com/playlist/{uris[0].split(':')[-1]}"
        return f"<p>Playlist trouvée :</p><a href='{url}' target='_blank'>{url}</a>"
    else:
        return "<p>Aucune playlist trouvée pour cette phrase.</p>"

# Si tu lances le fichier manuellement
def main():
    phrase = "J'ai besoin de me détendre après le travail."
    uris = trouver_playlists_depuis_phrase(phrase)

    if uris:
        print(f"Playlists trouvées ({len(uris)}):")
        for uri in uris:
            print("🎵", uri)
        jouer_playlist(uris[0])
    else:
        print("❌ Aucune playlist trouvée pour cette phrase.")



@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None  # Message d'erreur à afficher dans le template

    if request.method == 'POST':
        nom = request.form.get('nom')
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')

        print("Données reçues :", nom, email, mot_de_passe)

        if nom and email and mot_de_passe:
            hashed_password = generate_password_hash(mot_de_passe)

            conn = get_db_connection()
            cursor = conn.cursor()

            # Vérifie si l'email est déjà utilisé
            cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE email = ?", (email,))
            email_existant = cursor.fetchone()

            # Vérifie si le nom est déjà utilisé
            cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE nom = ?", (nom,))
            nom_existant = cursor.fetchone()

            if email_existant and nom_existant:
                message = "Désolé, ce nom et cet email sont déjà utilisés."
            elif email_existant:
                message = "Désolé, cet email est déjà enregistré."
            elif nom_existant:
                message = "Désolé, ce nom est déjà utilisé."

            if message:
                conn.close()
                return render_template('login.html', message=message)


            # Création du compte
            try:
                cursor.execute('''
                    INSERT INTO utilisateur (nom, email, mot_de_passe, a_choisi_gouts)
                    VALUES (?, ?, ?, 0)
                ''', (nom, email, hashed_password))
                conn.commit()

                session['user_id'] = nom
                session['first_login'] = True
                return redirect(url_for('spotify_login'))

            except Exception as e:
                print("Erreur DB:", e)

            finally:
                conn.close()

    return render_template('login.html', message=message)

@app.route('/spotify-login')
def spotify_login():
    nom = session.get('user_id')
    if not nom:
        return redirect(url_for('login'))

    # 🔐 Crée une nouvelle instance OAuth propre pour ce user
    sp_oauth = get_spotify_oauth_for_user(nom)
    auth_url = sp_oauth.get_authorize_url()

    # 🚀 Redirige vers l'authentification Spotify
    return redirect(auth_url)



@app.route('/callback')
def callback():
    nom = session.get('user_id')
    if not nom:
        return redirect(url_for('login'))

    sp_oauth = get_spotify_oauth_for_user(nom)
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

    from utils import save_spotify_tokens
    save_spotify_tokens(nom, token_info)

    sp = spotipy.Spotify(auth=token_info['access_token'])
    profile = sp.current_user()

    display_name = profile.get('display_name', 'Inconnu')
    spotify_id = profile.get('id', 'Inconnu')
    product = profile.get('product', 'inconnu')

    print("🎧 Spotify connecté :", display_name, "-", spotify_id, "-", product)

    if product != 'premium':
        return render_template("spotify_error.html", message="Compte non premium")

    session['spotify_type'] = product
    session['spotify_display_name'] = display_name

    # Redirection vers l’accueil, et non /preferences
    return redirect(url_for('index'))





    
@app.route('/play/<path:playlist_uri>')
def play_playlist(playlist_uri):
    access_token = get_valid_spotify_token()
    if not access_token:
        return redirect(url_for('spotify_login'))

    sp = spotipy.Spotify(auth=access_token)

    try:
        # Affiche les appareils connectés
        devices = sp.devices()
        print("Appareils visibles :", devices)

        device_id = None
        for d in devices['devices']:
            if d['is_active']:
                device_id = d['id']
                break

        if not device_id:
            return "Aucun appareil Spotify actif trouvé. Ouvre Spotify sur ton téléphone ou PC."

        # Lance la lecture sur l'appareil actif
        sp.start_playback(device_id=device_id, context_uri=playlist_uri)
        return f"Lecture lancée sur ton appareil : {device_id}"

    except Exception as e:
        print("Erreur de lecture Spotify :", e)
        return f"Erreur lors du lancement de la playlist : {e}"
    
    devices = sp.devices()
    print("🎯 Appareils trouvés :", [d['name'] for d in devices['devices']])





@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    message = None

    if request.method == 'POST':
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Recherche de l'utilisateur par email
        cursor.execute("SELECT nom, mot_de_passe FROM utilisateur WHERE email = ?", (email,))
        utilisateur = cursor.fetchone()
        conn.close()

        if utilisateur:
            nom_en_db, mot_de_passe_hash = utilisateur
            if check_password_hash(mot_de_passe_hash, mot_de_passe):
                session['user_id'] = nom_en_db
                return redirect(url_for('spotify_login'))
            else:
                message = "Mot de passe incorrect."
        else:
            message = "Aucun compte avec cet email."

    return render_template('connexion.html', message=message)





@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        gouts = request.form.getlist('genres')  # Les IDs des goûts cochés
        nom_utilisateur = session['user_id']

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # Récupère l’id de l’utilisateur
            cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE nom = ?", (nom_utilisateur,))
            utilisateur = cursor.fetchone()

            if utilisateur:
                utilisateur_id = utilisateur[0]
                # Insère chaque goût dans la table pivot
                for id_gout in gouts:
                    cursor.execute(
                        "INSERT INTO gout_utilisateur (id_utilisateur, id_gout) VALUES (?, ?)",
                        (utilisateur_id, id_gout)
                    )
                # Marque en base que l’utilisateur a choisi ses goûts
                cursor.execute(
                    "UPDATE utilisateur SET a_choisi_gouts = 1 WHERE id_utilisateur = ?",
                    (utilisateur_id,)
                )
                conn.commit()
        finally:
            conn.close()

        return redirect(url_for('index'))

    # Affiche simplement la page pour cocher les goûts
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_gout, nom FROM gout")
        gouts_disponibles = cursor.fetchall()
    finally:
        conn.close()

    return render_template('preferences.html', gouts=gouts_disponibles)

@app.route('/test-play')
def test_play():
    access_token = get_valid_spotify_token()
    if not access_token:
        return "❌ Token invalide"

    sp = spotipy.Spotify(auth=access_token)
    try:
        sp.start_playback(uris=["spotify:track:7ouMYWpwJ422jRcDASZB7P"])  # chanson universelle
        return "✅ Lecture lancée"
    except Exception as e:
        return f"❌ Erreur de lecture : {e}"

    
@app.route('/devices')
def devices():
    access_token = get_valid_spotify_token()
    if not access_token:
        return "❌ Aucun token valide"

    sp = spotipy.Spotify(auth=access_token)
    devices = sp.devices().get('devices', [])
    if not devices:
        return "❌ Aucun appareil détecté"
    
    return "<br>".join([f"✅ {d['name']} - type: {d['type']}" for d in devices])


def get_spotify_user_name():
    access_token = session.get('access_token')
    if not access_token:
        return None

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("display_name")  # ou data["id"] si pas de nom public
    else:
        print("⚠️ Impossible de récupérer les infos Spotify :", response.text)
        return None
    
# delete user 
def supprimer_utilisateur(id_utilisateur):
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../database/music.db"))
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM gout_utilisateur WHERE id_utilisateur = ?", (id_utilisateur,))
        print("🗑️ Suppression gout_utilisateur :", cursor.rowcount)

        cursor.execute("DELETE FROM utilisateur WHERE id_utilisateur = ?", (id_utilisateur,))
        print("🗑️ Suppression utilisateur :", cursor.rowcount)

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Erreur suppression : {e}")
        return False
    finally:
        if conn:
            conn.close()


@app.route('/delete_account', methods=['POST'])
def delete_account():
    user_name = session.get('user_id')
    print(f"👤 Tentative de suppression pour : {user_name}")

    if not user_name:
        flash("Aucun utilisateur connecté.")
        return redirect(url_for('index'))

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../database/music.db"))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE nom = ?", (user_name,))
        result = cursor.fetchone()
        print("🔍 Résultat SELECT :", result)

        if result:
            id_utilisateur = result[0]
            if supprimer_utilisateur(id_utilisateur):
                session.clear()
                flash("✅ Compte supprimé.")
            else:
                flash("❌ Échec suppression.")
        else:
            flash("❌ Utilisateur non trouvé.")
    except sqlite3.Error as e:
        flash(f"❌ Erreur DB : {e}")
    finally:
        conn.close()

    return redirect(url_for('login'))



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Table pour stocker les playlists en vedette
    # Sélectionner une playlist aléatoire
@app.route('/get-random-featured-playlist')
def get_random_featured_playlist():
    """Retourne une playlist aléatoire parmi celles en vedette"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupérer toutes les playlists en vedette
        cursor.execute("SELECT uri, titre FROM featured_playlists")
        playlists = cursor.fetchall()
        conn.close()
        
        if not playlists:
            # Playlist par défaut si aucune n'est configurée
            return jsonify({
                "uri": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
                "name": "Today's Top Hits"
            })
        
        # Sélectionner une playlist aléatoire
        import random
        playlist = random.choice(playlists)
        
        return jsonify({
            "uri": playlist[0],
            "name": playlist[1]
        })
    except Exception as e:
        print(f"Erreur lors de la récupération d'une playlist aléatoire: {e}")
        return jsonify({
            "uri": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
            "name": "Today's Top Hits"
        })



if __name__ == '__main__':
    # Change ici si tu veux tester localement en ligne de commande ou lancer le serveur
    # main()  # ← Décommente pour tester en CLI
    app.run(debug=True)  # ← Active l'interface web
