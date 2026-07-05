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
    session_id = request.args.get("sessionId")
    name1 = request.args.get("person1")
    name2 = request.args.get("person2")

    # 1. Trouver les IDs des deux personnes
    p1 = db.individuals.find_one({"sessionId": session_id, "name": name1})
    p2 = db.individuals.find_one({"sessionId": session_id, "name": name2})
    
    if not p1 or not p2: return jsonify([])

    start_id = p1['id']
    end_id = p2['id']

    # 2. Algorithme BFS pour trouver le chemin
    queue = [[start_id]]
    visited = {start_id}

    while queue:
        path = queue.pop(0)
        current_id = path[-1]

        if current_id == end_id:
            # Conversion des IDs en noms pour le frontend
            result = []
            for i, p_id in enumerate(path):
                indiv = db.individuals.find_one({"sessionId": session_id, "id": p_id})
                result.append({"name": indiv['name'], "level": i})
            return jsonify(result)

        # Trouver les familles de la personne courante
        families = db.families.find({"sessionId": session_id, "$or": [{"husb": current_id}, {"wife": current_id}, {"chil": current_id}]})
        
        for fam in families:
            # Extraire tous les membres liés à cette famille
            neighbors = []
            if fam.get('husb'): neighbors.append(fam['husb'])
            if fam.get('wife'): neighbors.append(fam['wife'])
            if fam.get('chil'): neighbors.extend(fam['chil'])
            
            for neighbor in neighbors:
                if neighbor not in visited and neighbor != current_id:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)

    return jsonify([]) # Aucun chemin trouvé

if __name__ == "__main__":
    app.run(debug=True)