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

# Route qui reçoit les données parsées par le navigateur
@app.route("/api/save_data", methods=["POST"])
def save_data():
    data = request.get_json()
    individuals = data.get("individuals", [])
    
    expire_at = datetime.utcnow() + timedelta(hours=1)
    documents = []
    
    for ind in individuals:
        # 'name' est extrait côté client par gedcom-js
        name = ind.get('name', 'Inconnu')
        documents.append({
            "fullname": name,
            "expireAt": expire_at
        })
    
    if documents:
        persons_collection.insert_many(documents)
        
    return jsonify({"success": True})

@app.route("/api/personnes")
def api_personnes():
    q = request.args.get("q", "")
    cursor = persons_collection.find({"fullname": {"$regex": q, "$options": "i"}}).limit(10)
    return jsonify([doc["fullname"] for doc in cursor])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)