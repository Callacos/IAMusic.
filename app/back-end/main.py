from flask import Flask, request, send_from_directory, render_template_string
from flask import render_template
from flask import session, redirect, url_for
from ia import trouver_playlists_depuis_phrase
from spotify import jouer_playlist
import os
import sqlite3
from werkzeug.security import generate_password_hash

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
                return redirect(url_for('preferences'))

            except Exception as e:
                print("Erreur DB:", e)

            finally:
                conn.close()

    return render_template('login.html', message=message)


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





if __name__ == '__main__':
    # Change ici si tu veux tester localement en ligne de commande ou lancer le serveur
    # main()  # ← Décommente pour tester en CLI
    app.run(debug=True)  # ← Active l'interface web
