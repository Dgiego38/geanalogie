from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import gzip
import json

app = Flask(__name__)
load_dotenv()

# Connexion MongoDB
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.genealogie
persons_collection = db.persons

# Index TTL pour suppression auto après 1 heure
persons_collection.create_index("expireAt", expireAfterSeconds=0)
# Index pour accélérer les recherches par session
persons_collection.create_index("sessionId") 

@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/menu")
def accueil():
    return render_template("index.html")

@app.route("/chemin")
def chemin():
    return render_template("chemin.html")

# Route qui reçoit les données compressées (GZIP) et parsées par lots
@app.route("/api/save_data", methods=["POST"])
def save_data():
    try:
        # 1. Vérification des données entrantes
        compressed_data = request.data
        if not compressed_data:
            print("ERREUR : Aucune donnée reçue.")
            return jsonify({"success": False, "error": "No data received"}), 400

        # 2. Décompression manuelle du flux GZIP reçu[cite: 2]
        decompressed_data = gzip.decompress(compressed_data)
        data = json.loads(decompressed_data.decode('utf-8'))
        
        session_id = data.get("sessionId")
        individuals = data.get("individuals", [])
        is_first_batch = data.get("isFirstBatch", False)
        
        print(f"DEBUG: Lot reçu | Session: {session_id} | Individus: {len(individuals)} | FirstBatch: {is_first_batch}")

        # Vérification critique
        if not session_id:
            print("ERREUR : sessionId manquant dans le JSON.")
            return jsonify({"success": False, "error": "Missing sessionId"}), 400

        # 3. Si c'est le premier lot, on nettoie les anciennes données de cette session[cite: 2]
        if is_first_batch:
            deleted = persons_collection.delete_many({"sessionId": session_id})
            print(f"DEBUG: Nettoyage initial | {deleted.deleted_count} anciens documents supprimés.")
        
        expire_at = datetime.utcnow() + timedelta(hours=1)
        
        # 4. Préparation des documents avec le sessionId[cite: 2]
        documents = [
            {
                "fullname": ind.get('name', 'Inconnu'), 
                "sessionId": session_id, 
                "expireAt": expire_at
            } 
            for ind in individuals
        ]
        
        # 5. Insertion dans MongoDB avec capture d'erreur
        if documents:
            try:
                result = persons_collection.insert_many(documents)
                print(f"DEBUG: SUCCÈS | {len(result.inserted_ids)} individus insérés dans MongoDB.")
            except Exception as db_err:
                print(f"ERREUR MONGODB LORS DE L'INSERTION : {db_err}")
                return jsonify({"success": False, "error": str(db_err)}), 500
        else:
            print("AVERTISSEMENT : La liste 'documents' est vide, rien à insérer.")
            
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"ERREUR SERVEUR GLOBALE : {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/personnes")
def api_personnes():
    session_id = request.args.get("sessionId")
    q = request.args.get("q", "")
    
    # Recherche filtrée par sessionId pour isoler les utilisateurs[cite: 2]
    cursor = persons_collection.find({
        "sessionId": session_id, 
        "fullname": {"$regex": q, "$options": "i"}
    }).limit(10)
    
    return jsonify([doc["fullname"] for doc in cursor])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)