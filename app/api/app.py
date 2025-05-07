import sys
import os
import sqlite3
import subprocess
from flask import request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template_string
from flask import send_from_directory


# Ajout du chemin vers le dossier back-end
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'back-end')))

from flask import Flask, request, jsonify
from flask_cors import CORS
from ia import trouver_playlists_depuis_phrase
from spotify import jouer_playlist

app = Flask(__name__)
CORS(app)

@app.route('/phrase', methods=['POST'])
def recevoir_phrase():
    data = request.get_json()
    phrase = data.get('phrase', '')

    # 🛠️ Lancer run.sh automatiquement
    """try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'run.sh'))
        subprocess.run(["bash", script_path], check=True)
        print(f"✅ Script run.sh exécuté depuis {script_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution de run.sh : {e}")"""

    # 🎧 Traitement de la phrase
    uris = trouver_playlists_depuis_phrase(phrase)
    if uris:
        jouer_playlist(uris[0])
        return jsonify({"uri": uris[0]})
    else:
        return jsonify({"uri": None})
    
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

app.secret_key = "ma_clé_ultra_secrète"

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    mot_de_passe = data.get("mot_de_passe")
    nom = data.get("nom", "").strip()

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'music.db'))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id_utilisateur, mot_de_passe, a_choisi_gouts FROM utilisateur WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user:
        id_utilisateur, mot_hash, a_choisi_gouts = user
        if check_password_hash(mot_hash, mot_de_passe):
            session["utilisateur_id"] = id_utilisateur
            if a_choisi_gouts:
                return jsonify({"status": "ok", "redirect": "/app"})
            else:
                return jsonify({"status": "ok", "redirect": "/preferences"})
        else:
            return jsonify({"status": "erreur", "message": "Mot de passe incorrect"})
    else:
        if not nom:
            return jsonify({"status": "erreur", "message": "Le nom est requis pour créer un compte."})

        mot_hash = generate_password_hash(mot_de_passe)
        cursor.execute(
            "INSERT INTO utilisateur (email, mot_de_passe, a_choisi_gouts, nom) VALUES (?, ?, 0, ?)",
            (email, mot_hash, nom)
        )
        conn.commit()
        id_utilisateur = cursor.lastrowid
        session["utilisateur_id"] = id_utilisateur
        return jsonify({"status": "ok", "redirect": "/preferences"})
    
@app.route('/login', methods=['GET'])
def login_page():
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'front-end', 'login.html'))
    with open(file_path, 'r', encoding='utf-8') as f:
        return render_template_string(f.read())


@app.route('/preferences', methods=['POST'])
def preferences():
    data = request.get_json()
    genres = data.get("genres", [])

    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        return jsonify({"status": "erreur", "message": "Non connecté"})

    if not genres:
        return jsonify({"status": "erreur", "message": "Aucun style sélectionné."})

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'music.db'))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        for genre_id in genres:
            cursor.execute("INSERT INTO gout_utilisateur (id_utilisateur, id_gout) VALUES (?, ?)", (utilisateur_id, genre_id))
        
        cursor.execute("UPDATE utilisateur SET a_choisi_gouts = 1 WHERE id_utilisateur = ?", (utilisateur_id,))
        conn.commit()
        return jsonify({"status": "ok"})
    except sqlite3.Error as e:
        return jsonify({"status": "erreur", "message": f"Erreur DB : {e}"})
    finally:
        conn.close()

@app.route('/preferences', methods=['GET'])
def preferences_page():
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'front-end', 'preferences.html'))
    with open(file_path, 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

@app.route('/style.css')
def serve_css():
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'front-end'), 'style.css')


if __name__ == "__main__":
    app.run(debug=True)
