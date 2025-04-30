from ia import trouver_playlists_depuis_phrase
from spotify import jouer_playlist  # cf. fichier à part spotify.py

def main():
    phrase = "J'ai besoin de me détendre après le travail."
    uris = trouver_playlists_depuis_phrase(phrase)

    if uris:
        print(f"Playlists trouvées ({len(uris)}):")
        for uri in uris:
            print("🎵", uri)
        jouer_playlist(uris[0])  # Lecture de la première playlist
    else:
        print("❌ Aucune playlist trouvée pour cette phrase.")

if __name__ == "__main__":
    main()
