from flask import Flask, render_template, request, jsonify
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
import tempfile
import os

app = Flask(__name__)

# Gestion globale du parser pour éviter de recharger le fichier à chaque requête
gedcom_parser = None

def get_parser():
    global gedcom_parser
    return gedcom_parser

@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/upload_ged", methods=["POST"])
def upload_ged():
    global gedcom_parser
    fichier = request.files.get("file")
    if not fichier:
        return jsonify({"success": False, "message": "Aucun fichier reçu"})

    # Stockage temporaire du fichier
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".ged")
    fichier.save(temp.name)

    # Initialisation du parser
    gedcom_parser = Parser()
    gedcom_parser.parse_file(temp.name, False)
    
    print("GEDCOM chargé en mémoire")
    return jsonify({"success": True})

@app.route("/menu")
def accueil():
    return render_template("index.html")

@app.route("/chemin")
def chemin():
    if get_parser() is None:
        return "Veuillez charger un GEDCOM d'abord"
    return render_template("chemin.html")

@app.route("/chemin_result")
def chemin_result():
    parser = get_parser()
    if parser is None:
        return jsonify([])

    person1 = request.args.get("person1")
    person2 = request.args.get("person2")

    # Trouver les objets Individuals
    p1 = None
    p2 = None
    for indiv in parser.get_root_child_elements():
        if isinstance(indiv, IndividualElement):
            prenom, nom = indiv.get_name()
            full = f"{prenom} {nom}"
            if full == person1: p1 = indiv
            if full == person2: p2 = indiv

    # Calculer le chemin via la méthode native de la bibliothèque
    if p1 and p2:
        try:
            # Cette méthode gère les liens familiaux nativement
            nodes = parser.display_relationship_path(p1, p2)
            
            # Formater le résultat pour ton frontend
            result = []
            for i, node in enumerate(nodes):
                result.append({"name": f"{node.get_name()[0]} {node.get_name()[1]}", "level": i})
            return jsonify(result)
        except Exception as e:
            print(f"Erreur calcul chemin: {e}")
            return jsonify([])

    return jsonify([])

@app.route("/api/personnes")
def api_personnes():
    parser = get_parser()
    if parser is None: return jsonify([])
    
    q = request.args.get("q", "").lower()
    personnes = []
    for indiv in parser.get_root_child_elements():
        if isinstance(indiv, IndividualElement):
            prenom, nom = indiv.get_name()
            full = f"{prenom} {nom}"
            if q in full.lower():
                personnes.append(full)
    return jsonify(personnes[:10])

if __name__ == "__main__":
    app.run(debug=True)