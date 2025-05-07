#!/bin/bash

# Se placer dans le répertoire racine du projet
cd "$(dirname "$0")"

# Initialiser la base de données si elle n'existe pas
if [ ! -f "./database/music.db" ]; then
    echo "📁 Initialisation de la base de données..."
    python3 ./database/init_db.py
fi

# Lancer le serveur Flask (et non back-end/main.py)
echo "🚀 Lancement de l'API Flask..."
cd api
python3 app.py
