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

# Index pour TTL et recherche rapide
persons_collection.create_index("expireAt", expireAfterSeconds=0)
persons_collection.create_index("sessionId") # Crucial pour l'isolation et la performance

@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/menu")
def accueil():
    return render_template("index.html")

@app.route("/chemin")
def chemin():
    return render_template("chemin.html")

@app.route("/api/save_data", methods=["POST"])
def save_data():
    # Décompression des données
    compressed_data = request.data
    decompressed_data = gzip.decompress(compressed_data)
    data = json.loads(decompressed_data.decode('utf-8'))
    
    session_id = data.get("sessionId")
    individuals = data.get("individuals", [])
    is_first_batch = data.get("isFirstBatch", False)
    
    # Nettoyage : suppression des anciennes données uniquement pour cette session
    if is_first_batch and session_id:
        persons_collection.delete_many({"sessionId": session_id})
    
    expire_at = datetime.utcnow() + timedelta(hours=1)
    
    # Insertion des documents avec l'étiquette sessionId
    documents = [
        {"fullname": ind.get('name', 'Inconnu'), "sessionId": session_id, "expireAt": expire_at} 
        for ind in individuals
    ]
    
    if documents:
        persons_collection.insert_many(documents)
    return jsonify({"success": True})

@app.route("/api/personnes")
def api_personnes():
    # Récupération du sessionId depuis l'URL (ex: /api/personnes?sessionId=xyz&q=jean)
    session_id = request.args.get("sessionId")
    q = request.args.get("q", "")
    
    # Recherche filtrée par sessionId pour ne renvoyer que les données de l'utilisateur[cite: 6]
    cursor = persons_collection.find({
        "sessionId": session_id, 
        "fullname": {"$regex": q, "$options": "i"}
    }).limit(10)
    
    return jsonify([doc["fullname"] for doc in cursor])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)