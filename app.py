from flask import Flask, render_template, request, jsonify
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
import tempfile
import os

app = Flask(__name__)

# Variable globale pour stocker le parser en mémoire
gedcom_parser = None

@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/upload_ged", methods=["POST"])
def upload_ged():
    global gedcom_parser
    fichier = request.files.get("file")
    if not fichier:
        return jsonify({"success": False, "message": "Aucun fichier reçu"})

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".ged")
    fichier.save(temp.name)
    
    # Parsing immédiat
    gedcom_parser = Parser()
    gedcom_parser.parse_file(temp.name, False)
    
    return jsonify({"success": True})

@app.route("/menu")
def accueil():
    return render_template("index.html")

@app.route("/chemin")
def chemin():
    return render_template("chemin.html")

@app.route("/chemin_result")
def chemin_result():
    if not gedcom_parser: return jsonify([])
    
    person1 = request.args.get("person1")
    person2 = request.args.get("person2")
    
    # Recherche des objets personnes par nom
    p1, p2 = None, None
    for indiv in gedcom_parser.get_root_child_elements():
        if isinstance(indiv, IndividualElement):
            full = f"{indiv.get_name()[0]} {indiv.get_name()[1]}"
            if full == person1: p1 = indiv
            if full == person2: p2 = indiv
            
    if p1 and p2:
        # La magie de la bibliothèque gedcom
        nodes = gedcom_parser.display_relationship_path(p1, p2)
        # On formate le retour pour ton JS
        return jsonify([{"name": f"{n.get_name()[0]} {n.get_name()[1]}", "level": i} for i, n in enumerate(nodes)])
    return jsonify([])

@app.route("/api/personnes")
def api_personnes():
    if not gedcom_parser: return jsonify([])
    q = request.args.get("q", "").lower()
    personnes = []
    for indiv in gedcom_parser.get_root_child_elements():
        if isinstance(indiv, IndividualElement):
            full = f"{indiv.get_name()[0]} {indiv.get_name()[1]}"
            if q in full.lower():
                personnes.append(full)
    return jsonify(personnes[:10])

if __name__ == "__main__":
    app.run(debug=True)