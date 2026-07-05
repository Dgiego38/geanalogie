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
    p1 = db.individuals.find_one({"sessionId": session_id, "name": request.args.get("person1")})
    p2 = db.individuals.find_one({"sessionId": session_id, "name": request.args.get("person2")})
    if not p1 or not p2: return jsonify([])
    
    # Algorithme BFS simplifié
    queue = [[p1['id']]]
    visited = {p1['id']}
    while queue:
        path = queue.pop(0)
        curr = path[-1]
        if curr == p2['id']:
            result = [{"name": db.individuals.find_one({"id": pid})['name'], "level": i} for i, pid in enumerate(path)]
            return jsonify(result)
        
        fams = db.families.find({"sessionId": session_id, "$or": [{"husb": curr}, {"wife": curr}, {"chil": curr}]})
        for f in fams:
            neighbors = [x for x in [f.get('husb'), f.get('wife')] + f.get('chil', []) if x and x != curr]
            for n in neighbors:
                if n not in visited:
                    visited.add(n)
                    queue.append(path + [n])
    return jsonify([])

if __name__ == "__main__": app.run(debug=True)