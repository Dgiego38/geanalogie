from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

# Connexion MongoDB
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.genealogie
persons_collection = db.persons

# Index TTL pour suppression auto après 1 heure
persons_collection.create_index("expireAt", expireAfterSeconds=0)

@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/menu")
def accueil():
    return render_template("index.html")

@app.route("/chemin")
def chemin():
    return render_template("chemin.html")

# Route qui reçoit les données parsées par lots (batches)
@app.route("/api/save_data", methods=["POST"])
def save_data():
    data = request.get_json()
    session_id = data.get("sessionId")
    individuals = data.get("individuals", [])
    is_first_batch = data.get("isFirstBatch", False)
    
    # Si c'est le premier lot, on nettoie les anciennes données de cette session
    if is_first_batch:
        persons_collection.delete_many({"sessionId": session_id})
    
    expire_at = datetime.utcnow() + timedelta(hours=1)
    
    # Préparation des documents avec le sessionId
    documents = [
        {
            "fullname": ind.get('name', 'Inconnu'), 
            "sessionId": session_id, 
            "expireAt": expire_at
        } 
        for ind in individuals
    ]
    
    if documents:
        persons_collection.insert_many(documents)
        
    return jsonify({"success": True})

@app.route("/api/personnes")
def api_personnes():
    session_id = request.args.get("sessionId")
    q = request.args.get("q", "")
    
    # Recherche filtrée par sessionId pour isoler les utilisateurs
    cursor = persons_collection.find({
        "sessionId": session_id, 
        "fullname": {"$regex": q, "$options": "i"}
    }).limit(10)
    
    return jsonify([doc["fullname"] for doc in cursor])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)