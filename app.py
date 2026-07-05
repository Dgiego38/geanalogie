from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import gzip
import json
import re

app = Flask(__name__)
load_dotenv()

# Connexion MongoDB
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.genealogie

# Fonction utilitaire pour nettoyer les IDs (enlève les '@' pour comparer)
def normalize_id(val):
    return val.replace('@', '') if isinstance(val, str) else val

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
    q = request.args.get("q", "")
    # Regex insensible à la casse
    cursor = db.individuals.find({"sessionId": session_id, "name": {"$regex": re.escape(q), "$options": "i"}}).limit(10)
    return jsonify([doc["name"] for doc in cursor])

# --- Logique de recherche de chemin (Générique) ---
@app.route("/chemin_result")
def chemin_result():
    session_id = request.args.get("sessionId")
    name1 = request.args.get("person1")
    name2 = request.args.get("person2")

    # Recherche insensible à la casse avec regex
    p1 = db.individuals.find_one({"sessionId": session_id, "name": {"$regex": f"^{re.escape(name1)}$", "$options": "i"}})
    p2 = db.individuals.find_one({"sessionId": session_id, "name": {"$regex": f"^{re.escape(name2)}$", "$options": "i"}})
    
    if not p1 or not p2: return jsonify([])

    # Utilisation des IDs normalisés
    start_id = normalize_id(p1['id'])
    end_id = normalize_id(p2['id'])

    queue = [[start_id]]
    visited = {start_id}

    while queue:
        path = queue.pop(0)
        current_id = path[-1]

        if current_id == end_id:
            result = []
            for i, p_id in enumerate(path):
                # On cherche en tenant compte que l'ID en base peut avoir des '@'
                indiv = db.individuals.find_one({
                    "sessionId": session_id, 
                    "$expr": {"$eq": [{"$replaceRoot": {"newRoot": "$$ROOT"}}, {"$replaceRoot": {"newRoot": "$$ROOT"}}]} # Astuce : chercher dynamiquement
                })
                # Plus simple : on boucle pour trouver celui qui matche le id normalisé
                all_inds = db.individuals.find({"sessionId": session_id})
                found = next((x for x in all_inds if normalize_id(x['id']) == p_id), None)
                if found:
                    result.append({"name": found['name'], "level": i})
            return jsonify(result)

        # Chercher les familles où la personne est présente (husb, wife, chil)
        # On doit récupérer toutes les familles et filtrer en Python pour gérer la normalisation des IDs
        all_fams = db.families.find({"sessionId": session_id})
        for fam in all_fams:
            # Normalisation des membres de la famille
            husb = normalize_id(fam.get('husb', ''))
            wife = normalize_id(fam.get('wife', ''))
            children = [normalize_id(c) for c in fam.get('chil', [])]
            
            # Si current_id est dans cette famille, on ajoute les autres membres comme voisins
            if current_id in [husb, wife] or current_id in children:
                neighbors = [n for n in [husb, wife] + children if n and n != current_id]
                for neighbor in neighbors:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        new_path = list(path)
                        new_path.append(neighbor)
                        queue.append(new_path)

    return jsonify([])

if __name__ == "__main__":
    app.run(debug=True)