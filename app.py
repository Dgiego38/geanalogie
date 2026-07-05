from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import gzip, json, os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.genealogie

@app.route("/")
def upload_page(): return render_template("upload.html")

@app.route("/menu")
def accueil(): return render_template("index.html")

@app.route("/chemin")
def chemin(): return render_template("chemin.html")

# Route de réception des données parsées par le client[cite: 1]
@app.route("/api/save_data", methods=["POST"])
def save_data():
    compressed_data = request.data
    data = json.loads(gzip.decompress(compressed_data).decode('utf-8'))
    session_id = data.get("sessionId")
    
    # Nettoyage ancienne session
    db.individuals.delete_many({"sessionId": session_id})
    db.families.delete_many({"sessionId": session_id})
    
    if data["individuals"]:
        for ind in data["individuals"]: ind.update({"sessionId": session_id})
        db.individuals.insert_many(data["individuals"])
    if data["families"]:
        for fam in data["families"]: fam.update({"sessionId": session_id})
        db.families.insert_many(data["families"])
    return jsonify({"success": True})

# Recherche de personnes pour l'autocomplete[cite: 1, 5]
@app.route("/api/personnes")
def api_personnes():
    session_id = request.args.get("sessionId")
    q = request.args.get("q", "").lower()
    cursor = db.individuals.find({"sessionId": session_id, "name": {"$regex": q, "$options": "i"}}).limit(10)
    return jsonify([doc["name"] for doc in cursor])

# Logique de recherche de chemin
@app.route("/chemin_result")
def chemin_result():
    session_id = request.args.get("sessionId")
    p1_name = request.args.get("person1")
    p2_name = request.args.get("person2")

    # 1. On récupère juste les IDs (Léger en RAM)
    p1 = db.individuals.find_one({"sessionId": session_id, "name": p1_name}, {"id": 1})
    p2 = db.individuals.find_one({"sessionId": session_id, "name": p2_name}, {"id": 1})
    if not p1 or not p2: return jsonify([])

    # 2. On utilise l'Aggregation Pipeline pour que MongoDB fasse le "BFS"
    # Cela évite de charger des milliers de documents en RAM
    pipeline = [
        {"$match": {"id": p1['id'], "sessionId": session_id}},
        {"$graphLookup": {
            "from": "families",
            "startWith": "$id",
            "connectFromField": "id",
            "connectToField": "chil", # ou husb/wife selon la structure
            "as": "path",
            "maxDepth": 10,
            "depthField": "numLinks"
        }}
    ]
    
    # Exécution : Ton serveur Python ne fait que transmettre l'ordre
    # MongoDB utilise ses index pour trouver le chemin.
    result = list(db.individuals.aggregate(pipeline))
    
    return jsonify(result)

if __name__ == "__main__": app.run(debug=True)