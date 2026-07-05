from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import gzip
import json

app = Flask(__name__)
load_dotenv()

# Connexion MongoDB
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.genealogie

# ------------------------------------------------------------------
# Route de réception des données parsées (Le chaînon manquant)
# ------------------------------------------------------------------
@app.route("/api/save_data", methods=["POST"])
def save_data():
    # 1. Récupération du flux compressé envoyé par upload_2.html
    compressed_data = request.data
    
    # 2. Décompression
    decompressed_data = gzip.decompress(compressed_data)
    data = json.loads(decompressed_data.decode('utf-8'))
    
    session_id = data.get("sessionId")
    individuals = data.get("individuals", [])
    families = data.get("families", [])
    
    # 3. Nettoyage de l'ancienne session (si c'est le premier lot)
    if data.get("isFirstBatch"):
        db.individuals.delete_many({"sessionId": session_id})
        db.families.delete_many({"sessionId": session_id})
    
    # 4. Insertion dans MongoDB
    if individuals:
        for ind in individuals:
            ind.update({"sessionId": session_id})
        db.individuals.insert_many(individuals)
        
    if families:
        for fam in families:
            fam.update({"sessionId": session_id})
        db.families.insert_many(families)
        
    return jsonify({"success": True})

# ------------------------------------------------------------------
# Route de recherche (pour que ton app.js fonctionne)
# ------------------------------------------------------------------
@app.route("/api/personnes")
def api_personnes():
    session_id = request.args.get("sessionId")
    q = request.args.get("q", "").lower()
    
    # Recherche dans la base de données
    cursor = db.individuals.find({
        "sessionId": session_id,
        "name": {"$regex": q, "$options": "i"} 
    }).limit(10)
    
    return jsonify([doc["name"] for doc in cursor])

# ------------------------------------------------------------------
# Routes de navigation
# ------------------------------------------------------------------
@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/menu")
def accueil():
    return render_template("index.html")

@app.route("/chemin")
def chemin():
    return render_template("chemin.html")

if __name__ == "__main__":
    app.run(debug=True)