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

# Index pour TTL et recherche rapide sur les nouvelles collections
db.individuals.create_index("expireAt", expireAfterSeconds=0)
db.individuals.create_index("sessionId")
db.families.create_index("expireAt", expireAfterSeconds=0)
db.families.create_index("sessionId")

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
    compressed_data = request.data
    decompressed_data = gzip.decompress(compressed_data)
    data = json.loads(decompressed_data.decode('utf-8'))
    
    session_id = data.get("sessionId")
    individuals = data.get("individuals", [])
    families = data.get("families", [])
    
    # Nettoyage ancienne session
    db.individuals.delete_many({"sessionId": session_id})
    db.families.delete_many({"sessionId": session_id})
    
    expire_at = datetime.utcnow() + timedelta(hours=1)
    
    # Stockage
    if individuals:
        for ind in individuals:
            ind.update({"sessionId": session_id, "expireAt": expire_at})
        db.individuals.insert_many(individuals)
        
    if families:
        for fam in families:
            fam.update({"sessionId": session_id, "expireAt": expire_at})
        db.families.insert_many(families)
        
    return jsonify({"success": True})

@app.route("/api/personnes")
def api_personnes():
    # Recherche corrigée : pointe vers db.individuals et utilise le champ "name"
    session_id = request.args.get("sessionId")
    q = request.args.get("q", "")
    
    cursor = db.individuals.find({
        "sessionId": session_id, 
        "name": {"$regex": "^" + q, "$options": "i"}
    }).limit(10)
    
    return jsonify([doc["name"] for doc in cursor])

@app.route("/chemin_result")
def chemin_result():
    # Récupération des paramètres
    session_id = request.args.get("sessionId")
    p1 = request.args.get("person1")
    p2 = request.args.get("person2")
    
    # Structure retournée (format JSON pour tree.js)
    data = {
        "name": p1,
        "dates": "1900-1970",
        "children": [
            {
                "name": p2,
                "dates": "1930-2000",
                "children": []
            }
        ]
    }
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)