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

# --- Routes de navigation ---
@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/menu")
def accueil():
    return render_template("index.html")

@app.route("/chemin")
def chemin():
    return render_template("chemin.html")

# --- API Data Management ---
@app.route("/api/save_data", methods=["POST"])
def save_data():
    compressed_data = request.data
    decompressed_data = gzip.decompress(compressed_data)
    data = json.loads(decompressed_data.decode('utf-8'))
    
    session_id = data.get("sessionId")
    individuals = data.get("individuals", [])
    families = data.get("families", [])
    
    if data.get("isFirstBatch"):
        db.individuals.delete_many({"sessionId": session_id})
        db.families.delete_many({"sessionId": session_id})
    
    if individuals:
        for ind in individuals: ind.update({"sessionId": session_id})
        db.individuals.insert_many(individuals)
    if families:
        for fam in families: fam.update({"sessionId": session_id})
        db.families.insert_many(families)
        
    return jsonify({"success": True})

@app.route("/api/personnes")
def api_personnes():
    session_id = request.args.get("sessionId")
    q = request.args.get("q", "").lower()
    cursor = db.individuals.find({"sessionId": session_id, "name": {"$regex": q, "$options": "i"}}).limit(10)
    return jsonify([doc["name"] for doc in cursor])

# --- Logique de recherche de chemin ---
@app.route("/chemin_result")
def chemin_result():
    # Ici, implémentation simplifiée du chemin entre 2 personnes
    # Note: Dans un vrai système, tu aurais besoin d'une recherche BFS dans ta base MongoDB
    return jsonify([{"name": request.args.get("person1"), "level": 0}, {"name": request.args.get("person2"), "level": 1}])

if __name__ == "__main__":
    app.run(debug=True)