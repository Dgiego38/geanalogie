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
    # ... (décompression identique)
    data = json.loads(decompressed_data.decode('utf-8'))
    individuals = data.get("individuals", [])
    is_first_batch = data.get("isFirstBatch", False)
    
    # Suppression globale au démarrage de l'import (ou selon votre besoin)
    if is_first_batch:
        persons_collection.delete_many({}) # Vide toute la collection
    
    expire_at = datetime.utcnow() + timedelta(hours=1)
    
    # Sans sessionId, on insère simplement les noms
    documents = [{"fullname": ind.get('name', 'Inconnu'), "expireAt": expire_at} for ind in individuals]
    
    if documents:
        persons_collection.insert_many(documents)
    return jsonify({"success": True})

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