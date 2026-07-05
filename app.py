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

@app.route("/api/save_data", methods=["POST"])
def save_data():
    compressed_data = request.data
    decompressed_data = gzip.decompress(compressed_data)
    data = json.loads(decompressed_data.decode('utf-8'))
    
    session_id = data.get("sessionId")
    individuals = data.get("individuals", [])
    is_first_batch = data.get("isFirstBatch", False)
    
    if is_first_batch and session_id:
        persons_collection.delete_many({"sessionId": session_id})
    
    expire_at = datetime.utcnow() + timedelta(hours=1)
    
    documents = [
        {"fullname": ind.get('name', 'Inconnu'), "sessionId": session_id, "expireAt": expire_at} 
        for ind in individuals
    ]
    
    if documents:
        persons_collection.insert_many(documents)
    return jsonify({"success": True})

@app.route("/api/personnes")
def api_personnes():
    session_id = request.args.get("sessionId")
    q = request.args.get("q", "")
    
    # Le "^" force la recherche à ne correspondre qu'au début du nom
    cursor = persons_collection.find({
        "sessionId": session_id, 
        "fullname": {"$regex": "^" + q, "$options": "i"}
    }).limit(10)
    
    return jsonify([doc["fullname"] for doc in cursor])

@app.route("/chemin_result")
def chemin_result():
    # Ici, vous ajouterez votre logique d'algo de chemin
    session_id = request.args.get("sessionId")
    p1 = request.args.get("person1")
    p2 = request.args.get("person2")
    # Retour de test pour valider la connexion
    return jsonify([{"name": p1, "type": "root", "level": 0}, {"name": p2, "type": "node", "level": 1}])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)