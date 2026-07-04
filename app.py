from flask import Flask, render_template, request, jsonify
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import os

app = Flask(__name__)
load_dotenv()

# Connexion MongoDB
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.genealogie
persons_collection = db.persons

# Index TTL pour suppression auto après 1 heure
persons_collection.create_index("expireAt", expireAfterSeconds=0)

# Stockage global léger du parser (uniquement si le fichier est en RAM)
gedcom_parser = None

def get_parser():
    return gedcom_parser

@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/menu")
def accueil():
    return render_template("index.html")

@app.route("/process_blob", methods=["POST"])
def process_blob():
    global gedcom_parser
    blob_url = request.get_json()["url"]
    
    # Streaming du fichier GEDCOM pour éviter le crash mémoire[cite: 7]
    # Note : Le parser gedcom nécessite un fichier physique. 
    # Pour Vercel, on utilise un stream minimal ou on réoriente vers une lecture locale.
    r = requests.get(blob_url, stream=True)
    
    # Reconstruction des données pour MongoDB sans SQLite
    expire_at = datetime.utcnow() + timedelta(hours=1)
    documents = []
    
    # Initialisation du parser avec le flux
    gedcom_parser = Parser()
    # Note: Dans un environnement Vercel serverless, 
    # la persistance de 'gedcom_parser' est limitée.
    gedcom_parser.parse_file(blob_url, False) 

    for indiv in gedcom_parser.get_root_child_elements():
        if isinstance(indiv, IndividualElement):
            try:
                prenom, nom = indiv.get_name()
                documents.append({
                    "id": indiv.get_pointer(),
                    "fullname": f"{prenom} {nom}",
                    "expireAt": expire_at
                })
            except: pass

    if documents:
        persons_collection.insert_many(documents)
        
    return jsonify({"success": True})

@app.route("/chemin_result")
def chemin_result():
    parser = get_parser()
    if not parser: return jsonify([])
    
    p1_name = request.args.get("person1")
    p2_name = request.args.get("person2")
    
    p1, p2 = None, None
    for indiv in parser.get_root_child_elements():
        if isinstance(indiv, IndividualElement):
            fn, ln = indiv.get_name()
            full = f"{fn} {ln}"
            if full == p1_name: p1 = indiv
            if full == p2_name: p2 = indiv
            
    if p1 and p2:
        try: return jsonify(parser.display_relationship_path(p1, p2))
        except Exception as e: return jsonify({"error": str(e)})
    return jsonify([])

@app.route("/api/personnes")
def api_personnes():
    q = request.args.get("q", "")
    cursor = persons_collection.find({"fullname": {"$regex": q, "$options": "i"}}).limit(10)
    return jsonify([doc["fullname"] for doc in cursor])

@app.route("/personne")
def personne():
    parser = get_parser()
    if not parser: return "Veuillez charger un GEDCOM"
    
    nom_complet = request.args.get("nom")
    target = next((i for i in parser.get_root_child_elements() 
                   if isinstance(i, IndividualElement) and f"{i.get_name()[0]} {i.get_name()[1]}" == nom_complet), None)
    
    if not target: return "Personne introuvable"
    
    fn, ln = target.get_name()
    html = f"<h1>{fn} {ln}</h1><h3>Parents</h3>"
    for p in parser.get_parents(target, "ALL"):
        html += f"<p>{p.get_name()[0]} {p.get_name()[1]}</p>"
    html += "<h3>Enfants</h3>"
    for e in parser.get_enfants(target, "ALL"):
        html += f"<p>{e.get_name()[0]} {e.get_name()[1]}</p>"
    return html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)