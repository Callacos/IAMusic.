import requests
import time
import pickle
import os
import hashlib
import re
import nltk
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

# Cache simple pour les requêtes Ollama
ollama_cache = {}
CACHE_FILE = os.path.join(os.path.dirname(__file__), "ollama_cache.pkl")

# Charger le cache s'il existe
try:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            ollama_cache = pickle.load(f)
        print(f"📂 Cache Ollama chargé : {len(ollama_cache)} entrées")
except:
    print("⚠️ Cache Ollama non trouvé ou invalide, démarrage avec un cache vide")

def save_cache():
    """Sauvegarde le cache des réponses Ollama sur disque"""
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(ollama_cache, f)
        print(f"💾 Cache Ollama sauvegardé : {len(ollama_cache)} entrées")
    except Exception as e:
        print(f"⚠️ Erreur lors de la sauvegarde du cache : {e}")

def extract_keywords_with_ollama(user_phrase):
    """
    Utilise Ollama (Gemma 2B instruct) pour extraire des mots-clés musicaux d'une phrase utilisateur.
    """
    import requests, hashlib, time

    phrase_key = hashlib.md5(user_phrase.lower().encode()).hexdigest()
    if phrase_key in ollama_cache:
        print(f"📎 Cache utilisé pour : '{user_phrase}'")
        return ollama_cache[phrase_key]

    try:
        print("🔄 Vérification de la dispo d’Ollama...")
        check = requests.get("http://localhost:11434/api/version", timeout=1)
        if check.status_code != 200:
            return None
        print("✅ Ollama est dispo")

        prompt = f"""Give 1 to 3 short music-related **keywords**, comma-separated, that describe the **intention or emotion** behind this sentence:

"{user_phrase}"

 Respond ONLY with the keywords. No sentences, no quotes, no explanation.
Example: I need something relaxing → relax, calm, chill
Keywords:"""


        payload = {
            "model": "gemma:2b-instruct",
            "prompt": prompt,
            "temperature": 0.2,
            "top_p": 1,
            "top_k": 40,
            "max_tokens": 20,
            "stream": False
        }

        print(f"🤖 Envoi à Gemma : '{user_phrase}'")
        start = time.time()
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=15)
        duration = time.time() - start
        print(f"⏱️ Réponse en {duration:.2f}s")

        if response.status_code == 200:
            raw = response.json().get("response", "").strip()
            raw = re.sub(r"\d+\.\s*", "", raw)  # Supprime "1. ", "2. " etc.
            raw = raw.replace("\n", ",")  # Remplace les sauts de ligne par des virgules
            print(f"🔍 Réponse brute : '{raw}'")

            for prefix in ["keywords:", "mots-clés :", "→", "- "]:
                if raw.lower().startswith(prefix):
                    raw = raw[len(prefix):].strip()

            if not raw.strip():
                print("⚠️ Réponse IA vide ou inutile")
                return None

            keywords = [lemmatizer.lemmatize(k.strip().lower(), pos='v') for k in raw.split(",") if len(k.strip()) > 1]
            keywords = list(dict.fromkeys(keywords))[:3]

            if keywords:
                ollama_cache[phrase_key] = keywords
                if len(ollama_cache) % 5 == 0:
                    save_cache()
                print(f"✅ Mots-clés IA : {keywords}")
                return keywords
            else:
                print("⚠️ Aucun mot-clé après nettoyage")
                return None
        else:
            print(f"❌ Réponse KO : {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print("⏱️ Timeout Ollama")
        return None
    except Exception as e:
        print(f"❌ Erreur générale : {e}")
        return None

def warmup_ollama():
    """
    Préchauffe Ollama en effectuant une requête simple.
    À utiliser au démarrage de l'application.
    """
    print("🔥 Préchauffage d'Ollama...")
    try:
        # Simple requête pour charger le modèle en mémoire
        payload = {
            "model": "gemma:2b",
            "prompt": "Donne 3 mots-clés musicaux pour: détente",
            "stream": False
        }
        
        start = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate", 
            json=payload, 
            timeout=30
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ Ollama préchauffé en {duration:.2f} secondes")
            # Ajouter une entrée dans le cache pour "détente"
            result = response.json()
            keywords_text = result.get('response', '').strip()
            keywords = [k.strip().lower() for k in keywords_text.split(',')]
            if keywords and len(keywords) > 0:
                cache_key = hashlib.md5("détente".encode()).hexdigest()
                ollama_cache[cache_key] = keywords[:3]
            return True
        else:
            print(f"❌ Échec du préchauffage : {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors du préchauffage : {str(e)}")
        return False

# Si ce fichier est exécuté directement, effectuer un test
if __name__ == "__main__":
    # Préchauffer Ollama
    warmup_ollama()
    
    # Tester l'extraction de mots-clés
    test_phrases = [
        "Je suis stressé et j'ai besoin de me calmer",
        "Musique pour faire du sport",
        "Je veux danser toute la nuit"
    ]
    
    for phrase in test_phrases:
        print(f"\n🧪 Test avec la phrase: '{phrase}'")
        keywords = extract_keywords_with_ollama(phrase)
        print(f"📊 Résultat: {keywords}")
    
    # Sauvegarder le cache à la fin
    save_cache()

# Dictionnaire de synonymes
synonym_map = {
    "bouger": "bouge",
    "bougé": "bouge",
    "je veux bouge": "bouge",
    "danser": "bouge",
    "dance": "bouge",
    "rhythmic": "bouge",
    "calm": "relax",
    "chill": "relax",
    "peace": "relax",
    "relaxing": "relax",
    "tense": "stress",
    "anxious": "stress",
    "energetic": "énergie",
    "motivation": "énergie",
    "stressé": "stress",
    "crié": "crier",
    "scream": "crier",
    "sport": "sport",
    "muscu": "sport",
    "musculation": "sport",
    "gym": "sport",
    "entrainement": "sport",
    "training": "sport",
    "park": "linkin park",
    "linkin": "linkin park",
    "taff": "travail",
    "boulot": "travail",
    
}

def normalize_keywords(keywords):
    """Normalise une liste de mots-clés en appliquant lemmatisation et dédoublonnage"""
    if not keywords:
        return []
    
    try:
        # Lemmatisation des mots-clés
        lemmatized = []
        for k in keywords:
            try:
                lemmatized.append(lemmatizer.lemmatize(k.strip().lower(), pos='v'))
            except Exception as e:
                print(f"⚠️ Erreur de lemmatisation pour '{k}': {e}")
                lemmatized.append(k.strip().lower())
        
        # Supprimer les doublons tout en préservant l'ordre
        return list(dict.fromkeys(lemmatized))
    except Exception as e:
        print(f"⚠️ Erreur dans normalize_keywords: {e}")
        # En cas d'erreur, retourner les mots-clés originaux sans traitement
        return list(dict.fromkeys([k.strip().lower() for k in keywords]))