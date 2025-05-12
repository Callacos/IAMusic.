from flask import Flask, request, send_from_directory, render_template_string
from flask import render_template
from flask import session, redirect, url_for
from ia import trouver_playlists_depuis_phrase
from spotify import jouer_playlist
import os
import sqlite3
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from utils import get_valid_spotify_token, sp_oauth, get_spotify_profile
import spotipy
from utils import get_valid_spotify_token

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

    # ✅ Ceci sera bien exécuté si l'utilisateur est connecté
    profile = get_spotify_profile()
    if profile:
        print("🎧 Utilisateur Spotify :", profile['display_name'], "-", profile['id'], "-", profile['product'])
    else:
        print("⚠️ Aucun profil Spotify connecté ou token invalide.")

    return render_template('index.html')




# Route pour le fichier CSS
@app.route('/style.css')
def style():
    return send_from_directory('../front-end', 'style.css')

# Route qui reçoit la phrase du front-end
@app.route('/phrase', methods=['POST'])
def recevoir_phrase():
    data = request.get_json()
    phrase = data.get('phrase')

    uris = trouver_playlists_depuis_phrase(phrase)

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
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['spotify_token_info'] = token_info

    # Récupérer le profil utilisateur Spotify
    sp = spotipy.Spotify(auth=token_info['access_token'])
    profile = sp.current_user()

    # ✅ Utilisation sécurisée de .get() pour éviter KeyError
    display_name = profile.get('display_name', 'Inconnu')
    spotify_id = profile.get('id', 'Inconnu')
    product = profile.get('product', 'inconnu')

    print("🎧 Spotify connecté :", display_name, "-", spotify_id, "-", product)

    if product != 'premium':
        print("❌ COMPTE GRATUIT BLOQUÉ :", spotify_id)
        return "❌ Ce compte Spotify n'est pas Premium. IAMusic nécessite un compte Premium pour fonctionner."

    return redirect(url_for('preferences'))






def get_valid_spotify_token():
    token_info = session.get('spotify_token_info', None)

    if not token_info:
        return None

    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['spotify_token_info'] = token_info  # met à jour la session

    return token_info['access_token']


    
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
                session['first_login'] = False  # car il s’est déjà connecté
                return redirect(url_for('index'))
            else:
                message = "Mot de passe incorrect."
        else:
            message = "Aucun compte avec cet email."

    return render_template('connexion.html', message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))




@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        gouts = request.form.getlist('genres')  # <input name="genres" ...>
        nom_utilisateur = session['user_id']

        print("Genres sélectionnés :", gouts)
        print("Nom d'utilisateur :", nom_utilisateur)

        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            # Récupère l'id de l'utilisateur à partir du nom
            cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE nom = ?", (nom_utilisateur,))
            utilisateur = cursor.fetchone()
            print("Résultat SELECT utilisateur :", utilisateur)
            # Si l'utilisateur existe, on récupère son id

            if utilisateur:
                utilisateur_id = utilisateur[0]

                # Insère chaque goût sélectionné dans la table pivot
                for id_gout in gouts:
                    cursor.execute('''
                        INSERT INTO gout_utilisateur (id_utilisateur, id_gout)
                        VALUES (?, ?)
                    ''', (utilisateur_id, id_gout))

                # Met à jour le champ a_choisi_gouts
                cursor.execute('''
                    UPDATE utilisateur SET a_choisi_gouts = 1 WHERE id_utilisateur = ?
                ''', (utilisateur_id,))

                conn.commit()

        finally:
            conn.close()

        session['first_login'] = False
        return redirect(url_for('index'))

    # Si l'utilisateur a déjà choisi ses goûts, il va à l'accueil directement
    if not session.get('first_login'):
        return redirect(url_for('index'))

    # Affiche les goûts disponibles depuis la table `gout`
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
        return redirect(url_for('spotify_login'))

    sp = spotipy.Spotify(auth=access_token)
    try:
        sp.start_playback(uris=["spotify:track:7ouMYWpwJ422jRcDASZB7P"])  # un titre universel
        return "Test de lecture OK"
    except Exception as e:
        print("❌ Erreur Spotify :", e)
        return f"❌ Erreur : {e}"






if __name__ == '__main__':
    # Change ici si tu veux tester localement en ligne de commande ou lancer le serveur
    # main()  # ← Décommente pour tester en CLI
    app.run(debug=True)  # ← Active l'interface web
