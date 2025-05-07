import sqlite3
import os

def supprimer_utilisateur(id_utilisateur):
    db_path = os.path.join(os.path.dirname(__file__), "music.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Supprimer d'abord les goûts associés
        cursor.execute("DELETE FROM gout_utilisateur WHERE id_utilisateur = ?", (id_utilisateur,))
        # Supprimer ensuite l'utilisateur
        cursor.execute("DELETE FROM utilisateur WHERE id_utilisateur = ?", (id_utilisateur,))
        conn.commit()
        print(f"✅ Utilisateur {id_utilisateur} supprimé avec ses goûts.")
    except sqlite3.Error as e:
        print(f"❌ Erreur lors de la suppression : {e}")
    finally:
        conn.close()

# 🔧 Tu peux modifier cet ID pour tester un autre utilisateur
if __name__ == "__main__":
    supprimer_utilisateur(1)
