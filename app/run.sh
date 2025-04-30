#!/bin/bash

# Se placer dans le répertoire du script
cd "$(dirname "$0")"

# Initialiser la base de données si elle n'existe pas
if [ ! -f "./database/music.db" ]; then
    echo "Initialisation de la base de données..."
    python3 ./database/init_db.py
fi

# Lancer l'application
echo "Démarrage de l'application..."
cd back-end
python3 main.py