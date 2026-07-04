from flask import Flask, render_template, request, jsonify
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
import tempfile

app = Flask(__name__)

# ------------------------------------------------------------------
# GEDCOM chargé par l'utilisateur
# ------------------------------------------------------------------

gedcom_parser = None


# ------------------------------------------------------------------
# Upload initial
# ------------------------------------------------------------------

@app.route("/")
def upload_page():
    return render_template("upload.html")


@app.route("/upload_ged", methods=["POST"])
def upload_ged():

    global gedcom_parser

    fichier = request.files.get("file")

    if not fichier:
        return jsonify({
            "success": False,
            "message": "Aucun fichier reçu"
        })

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".ged"
    )

    fichier.save(temp.name)

    gedcom_parser = Parser()
    gedcom_parser.parse_file(temp.name, False)

    print("GEDCOM chargé")

    return jsonify({"success": True})


# ------------------------------------------------------------------
# Menu principal
# ------------------------------------------------------------------

@app.route("/menu")
def accueil():
    return render_template("index.html")


# ------------------------------------------------------------------
# Page chemin
# ------------------------------------------------------------------

@app.route("/chemin")
def chemin():

    if gedcom_parser is None:
        return "Veuillez charger un GEDCOM"

    return render_template("chemin.html")


# ------------------------------------------------------------------
# Recherche de chemin
# ------------------------------------------------------------------

@app.route("/chemin_result")
def chemin_result():

    global gedcom_parser

    if gedcom_parser is None:
        return jsonify([])

    person1 = request.args.get("person1")
    person2 = request.args.get("person2")

    p1 = None
    p2 = None

    for indiv in gedcom_parser.get_root_child_elements():

        if isinstance(indiv, IndividualElement):

            prenom, nom = indiv.get_name()
            full = f"{prenom} {nom}"

            if full == person1:
                p1 = indiv

            if full == person2:
                p2 = indiv

    if p1 and p2:

        try:
            nodes = gedcom_parser.display_relationship_path(
                p1,
                p2
            )

            return jsonify(nodes)

        except Exception as e:

            return jsonify({
                "error": str(e)
            })

    return jsonify([])


# ------------------------------------------------------------------
# Autocomplétion personnes
# ------------------------------------------------------------------

@app.route("/api/personnes")
def api_personnes():

    global gedcom_parser

    if gedcom_parser is None:
        return jsonify([])

    q = request.args.get(
        "q",
        ""
    ).lower()

    personnes = []

    for indiv in gedcom_parser.get_root_child_elements():

        if isinstance(
            indiv,
            IndividualElement
        ):

            prenom, nom = indiv.get_name()
            full = f"{prenom} {nom}"

            if q in full.lower():
                personnes.append(full)

    return jsonify(personnes[:10])


# ------------------------------------------------------------------
# Fiche personne
# ------------------------------------------------------------------

@app.route("/personne")
def personne():

    global gedcom_parser

    if gedcom_parser is None:
        return "Veuillez charger un GEDCOM"

    nom_complet = request.args.get("nom")

    personne = None

    for indiv in gedcom_parser.get_root_child_elements():

        if isinstance(indiv, IndividualElement):

            prenom, nom = indiv.get_name()
            full = f"{prenom} {nom}"

            if full == nom_complet:
                personne = indiv
                break

    if not personne:
        return "Personne introuvable"

    prenom, nom = personne.get_name()

    html = f"""
    <h1>{prenom} {nom}</h1>
    """

    html += "<h3>Parents</h3>"

    try:

        parents = gedcom_parser.get_parents(
            personne,
            "ALL"
        )

        for p in parents:

            fn, ln = p.get_name()

            html += f"<p>{fn} {ln}</p>"

    except:
        pass

    html += "<h3>Enfants</h3>"

    try:

        enfants = gedcom_parser.get_enfants(
            personne,
            "ALL"
        )

        for e in enfants:

            fn, ln = e.get_name()

            html += f"<p>{fn} {ln}</p>"

    except:
        pass

    return html


# ------------------------------------------------------------------
# Lancement local
# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=False)