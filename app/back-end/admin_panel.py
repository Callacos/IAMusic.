import sqlite3
import os
import getpass
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "music.db")
load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
))


def get_or_create_id(cursor, table, column, value):
    cursor.execute(f"SELECT id_{table} FROM {table} WHERE {column} = ?", (value,))
    result = cursor.fetchone()
    if result:
        return result[0]
    cursor.execute(f"INSERT INTO {table} ({column}) VALUES (?)", (value,))
    return cursor.lastrowid

def get_or_create_association(cursor, id_mot_cle, id_genre):
    cursor.execute("SELECT id_association FROM association WHERE id_mot_cle = ? AND id_genre = ?", (id_mot_cle, id_genre))
    result = cursor.fetchone()
    if result:
        return result[0]
    cursor.execute("INSERT INTO association (id_mot_cle, id_genre) VALUES (?, ?)", (id_mot_cle, id_genre))
    return cursor.lastrowid

def ajouter_playlist():
    uri = input("👉 Entrez l'URI Spotify : ").strip()
    genre = input("👉 À quel genre appartient cette playlist ? ").strip().lower()
    mot_cle = input("👉 Quel mot-clé lui correspond ? ").strip().lower()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        id_genre = get_or_create_id(cursor, "genre", "nom_genre", genre)
        id_mot_cle = get_or_create_id(cursor, "mot_cle", "mot", mot_cle)
        id_association = get_or_create_association(cursor, id_mot_cle, id_genre)
        cursor.execute("INSERT INTO playlist (uri, id_association) VALUES (?, ?)", (uri, id_association))
        conn.commit()
        print("✅ Playlist ajoutée avec succès !")
    except sqlite3.Error as e:
        print("❌ Erreur lors de l'ajout :", e)
    finally:
        conn.close()

def supprimer_playlist():
    uri = input("👉 Entrez l'URI de la playlist à supprimer : ").strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM playlist WHERE uri = ?", (uri,))
        conn.commit()
        print("✅ Playlist supprimée (si elle existait).")
    except sqlite3.Error as e:
        print("❌ Erreur :", e)
    finally:
        conn.close()

def bloquer_utilisateur():
    id_user = input("👉 ID de l'utilisateur à bloquer : ").strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE user SET bloque = 1 WHERE id_utilisateur = ?", (id_user,))
        conn.commit()
        print("✅ Utilisateur bloqué.")
    except sqlite3.Error as e:
        print("❌ Erreur :", e)
    finally:
        conn.close()

def debloquer_utilisateur():
    id_user = input("👉 ID de l'utilisateur à débloquer : ").strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE user SET bloque = 0 WHERE id_utilisateur = ?", (id_user,))
        conn.commit()
        print("✅ Utilisateur débloqué.")
    except sqlite3.Error as e:
        print("❌ Erreur :", e)
    finally:
        conn.close()
        
def authentifier_admin():
    mot_de_passe_attendu = "admin123"
    print("🔐 Accès au panneau d'administration IAMusic")
    mot_de_passe = getpass.getpass("Entrez le mot de passe : ")
    if mot_de_passe != mot_de_passe_attendu:
        print("❌ Accès refusé.")
        exit()
    print("✅ Accès autorisé.")

def definir_artiste_semaine():
    nom = input("🎤 Nom de l'artiste de la semaine : ")
    artiste = get_artist_info(nom)
    if artiste:
        print("\n➡️ Artiste trouvé :", artiste['nom'])
        print("🖼️ Image :", artiste['image'])
        print("📀 Albums récupérés :")
        for album in artiste['albums']:
            print("   -", album['nom'])

        # Ajoute les titres manuellement (optionnel)
        while True:
            titre = input("🎵 Ajouter un titre (laisser vide pour terminer) : ")
            if not titre:
                break
            uri = input("  ↪️ URI Spotify du titre : ")
            artiste['titres'].append({'nom': titre, 'uri': uri})

        enregistrer_artiste(artiste)

def get_artist_info(artist_name):
    results = sp.search(q=artist_name, type='artist', limit=1)
    if not results['artists']['items']:
        print("❌ Artiste introuvable.")
        return None

    artist = results['artists']['items'][0]
    artist_id = artist['id']
    image_url = artist['images'][0]['url'] if artist['images'] else None

    # Albums
    albums_data = sp.artist_albums(artist_id, album_type='album', limit=10)
    albums = []
    seen = set()
    for album in sorted(albums_data['items'], key=lambda a: a['release_date'], reverse=True):
        if album['name'] not in seen:
            seen.add(album['name'])
            albums.append({
                "nom": album["name"],
                "uri": album["uri"],
                "image": album["images"][0]["url"] if album["images"] else ""
            })
        if len(albums) >= 5:
            break
        return {
        "nom": artist["name"],
        "image": image_url,
        "albums": albums,
        "titres": []
    }

def enregistrer_artiste(data, fichier='artiste_semaine.json'):
    with open(fichier, 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ Données sauvegardées dans", fichier)

def gerer_playlists_vedette():
    print("\n=== Gestion des playlists en vedette ===")
    print("Ces playlists seront jouées aléatoirement quand un utilisateur clique sur le logo.")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    while True:
        print("\n1. Voir les playlists actuelles")
        print("2. Ajouter une playlist")
        print("3. Supprimer une playlist")
        print("4. Retour au menu principal")
        
        choix = input("Votre choix : ")
        
        if choix == "1":
            cursor.execute("SELECT id, uri, titre FROM featured_playlists")
            playlists = cursor.fetchall()
            
            if not playlists:
                print("Aucune playlist en vedette pour le moment.")
            else:
                print("\nPlaylists actuelles :")
                for p in playlists:
                    print(f"ID: {p[0]} | Titre: {p[2]} | URI: {p[1]}")
        
        elif choix == "2":
            uri = input("URI de la playlist Spotify : ").strip()
            titre = input("Nom de la playlist : ").strip()
            
            if uri and titre:
                try:
                    cursor.execute(
                        "INSERT INTO featured_playlists (uri, titre) VALUES (?, ?)",
                        (uri, titre)
                    )
                    conn.commit()
                    print("✅ Playlist ajoutée avec succès !")
                except sqlite3.Error as e:
                    print(f"❌ Erreur : {e}")
            else:
                print("❌ URI et titre sont obligatoires.")
        
        elif choix == "3":
            id_playlist = input("ID de la playlist à supprimer : ").strip()
            try:
                cursor.execute(
                    "DELETE FROM featured_playlists WHERE id = ?",
                    (id_playlist,)
                )
                conn.commit()
                print("✅ Playlist supprimée.")
            except sqlite3.Error as e:
                print(f"❌ Erreur : {e}")
        
        elif choix == "4":
            break
        
        else:
            print("❗ Option invalide.")
    
    conn.close()


def main():
    authentifier_admin()
    while True:
        print("\n=== IAMusic Admin Panel ===")
        print("1. Ajouter une playlist")
        print("2. Supprimer une playlist")
        print("3. Bloquer un utilisateur")
        print("4. Débloquer un utilisateur")
        print("5. Quitter")
        print("6. Mettre à jour l'artiste de la semaine")
        print("7. Gérer les playlists en vedette")


        choix = input("Sélectionnez une option : ")

        if choix == "1":
            ajouter_playlist()
        elif choix == "2":
            supprimer_playlist()
        elif choix == "3":
            bloquer_utilisateur()
        elif choix == "4":
            debloquer_utilisateur()
        elif choix == "5":
            print("À bientôt !")
            break
        elif choix == "6":
            definir_artiste_semaine()
        elif choix == "7":
            gerer_playlists_vedette()

        else:
            print("❗ Option invalide.")



            


if __name__ == "__main__":
    main()