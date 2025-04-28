import spacy
import sqlite3

# Chargement du modèle spaCy français
nlp = spacy.load("fr_core_news_sm")

# 🔎 1. Extraire les mots-clés depuis une phrase utilisateur
def extraire_mots_cles(phrase):
    doc = nlp(phrase)
    mots_cles = [
        token.lemma_.lower()
        for token in doc
        if token.pos_ in ["NOUN", "ADJ", "VERB", "PROPN"]
        and not token.is_stop
        and token.is_alpha
        and (token.ent_type_ in ["PERSON", "ORG", "GPE"] or not token.ent_type_)
    ]
    return mots_cles

#  2. Récupérer les playlists associées à ces mots-clés
def trouver_playlists_depuis_phrase(phrase):
    conn = sqlite3.connect("music.db")
    cursor = conn.cursor()

    mots = extraire_mots_cles(phrase)
    uris = []

    for mot in mots:
        # Récupérer id_mot_cle
        cursor.execute("SELECT id_mot_cle FROM mot_cle WHERE mot = ?", (mot,))
        result = cursor.fetchone()
        if result:
            id_mot_cle = result[0]

            # Récupérer tous les id_association liés à ce mot-clé
            cursor.execute("SELECT id_association FROM association WHERE id_mot_cle = ?", (id_mot_cle,))
            associations = cursor.fetchall()

            for (id_association,) in associations:
                # Récupérer les URI des playlists liées
                cursor.execute("SELECT uri FROM playlist WHERE id_association = ?", (id_association,))
                uris += [row[0] for row in cursor.fetchall()]

    conn.close()
    return uris
