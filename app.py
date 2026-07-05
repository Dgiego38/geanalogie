from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import gzip
import json

app = Flask(__name__)
load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client.genealogie
persons_collection = db.persons

# Index pour TTL et recherche
persons_collection.create_index("expireAt", expireAfterSeconds=0)

@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/menu")
def accueil():
    return render_template("index.html")

@app.route("/api/save_data", methods=["POST"])
def save_data():
    compressed_data = request.data
    decompressed_data = gzip.decompress(compressed_data)
    data = json.loads(decompressed_data.decode('utf-8'))
    
    individuals = data.get("individuals", [])
    is_first_batch = data.get("isFirstBatch", False)
    
    if is_first_batch:
        persons_collection.delete_many({}) # Vide la collection pour un nouvel import
    
    expire_at = datetime.utcnow() + timedelta(hours=1)
    
    documents = [{"fullname": ind.get('name', 'Inconnu'), "expireAt": expire_at} for ind in individuals]
    
    if documents:
        persons_collection.insert_many(documents)
    return jsonify({"success": True})

@app.route("/api/personnes")
def api_personnes():
    # Recherche globale sans sessionId
    q = request.args.get("q", "")
    cursor = persons_collection.find({"fullname": {"$regex": q, "$options": "i"}}).limit(10)
    return jsonify([doc["fullname"] for doc in cursor])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)