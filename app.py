from flask import Flask, render_template, request, jsonify
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from pymongo import MongoClient
from datetime import datetime, timedelta
import tempfile
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(
    os.getenv("MONGODB_URI")
)

db = client.genealogie

persons_collection = db.persons

persons_collection.create_index(
    "expireAt",
    expireAfterSeconds=0
)
app = Flask(__name__)

# ------------------------------------------------------------------
# GEDCOM chargé par l'utilisateur
# ------------------------------------------------------------------

gedcom_parser = None
gedcom_file = None
def construire_base_mongodb():

    persons_collection.delete_many({})

    expire_at = (
        datetime.utcnow()
        + timedelta(hours=1)
    )

    documents = []

    for indiv in gedcom_parser.get_root_child_elements():

        if isinstance(
            indiv,
            IndividualElement
        ):

            try:

                prenom, nom = indiv.get_name()

                documents.append({

                    "id":
                        indiv.get_pointer(),

                    "fullname":
                        f"{prenom} {nom}",

                    "expireAt":
                        expire_at
                })

            except:
                pass

    if documents:

        persons_collection.insert_many(
            documents
        )

    print(
        len(documents),
        "personnes importées"
    )

    print("BASE MONGODB CRÉÉE")

def construire_base_sqlite():

    if os.path.exists("genealogie.db"):
        os.remove("genealogie.db")

    conn = sqlite3.connect("genealogie.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE persons(
            id TEXT PRIMARY KEY,
            fullname TEXT
        )
    """)

    for indiv in gedcom_parser.get_root_child_elements():

        if isinstance(
            indiv,
            IndividualElement
        ):

            try:

                prenom, nom = indiv.get_name()

                cur.execute("""
                    INSERT INTO persons
                    VALUES (?, ?)
                """, (
                    indiv.get_pointer(),
                    f"{prenom} {nom}"
                ))

            except:
                pass

    conn.commit()
    conn.close()

    print("BASE SQLITE CRÉÉE")

def get_parser():

    global gedcom_parser
    global gedcom_file

    if gedcom_parser is None and gedcom_file:

        try:
            gedcom_parser = Parser()
            gedcom_parser.parse_file(
                gedcom_file,
                False
            )

            print("GEDCOM rechargé")

        except Exception as e:

            print(e)
            return None

    return gedcom_parser


# ------------------------------------------------------------------
# Upload initial
# ------------------------------------------------------------------

@app.route("/")
def upload_page():
    return render_template("upload.html")


@app.route("/upload_ged", methods=["POST"])
def upload_ged():

    global gedcom_parser
    global gedcom_file

    print("1 - Route upload appelée")

    fichier = request.files.get("file")

    if not fichier:

        print("2 - Aucun fichier reçu")

        return jsonify({
            "success": False,
            "message": "Aucun fichier reçu"
        })

    print(
        "3 - Fichier reçu :",
        fichier.filename
    )

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".ged"
    )

    print(
        "4 - Temp créé :",
        temp.name
    )

    try:

        fichier.save(temp.name)

        print("5 - Fichier sauvegardé")

        gedcom_file = temp.name

        print("6 - Début parsing")

        gedcom_parser = Parser()

        gedcom_parser.parse_file(
            gedcom_file,
            False
        )

        print("7 - Parsing terminé")

        print("8 - Construction MongoDB")

        construire_base_mongodb()

        print("9 - MongoDB terminée")

        print("10 - GEDCOM chargé")

        return jsonify({
            "success": True
        })

    except Exception as e:

        print(
            "ERREUR :",
            str(e)
        )

        return jsonify({
            "success": False,
            "message": str(e)
        })


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

    parser = get_parser()

    if parser is None:
        return "Veuillez charger un GEDCOM"

    return render_template("chemin.html")


# ------------------------------------------------------------------
# Recherche de chemin
# ------------------------------------------------------------------

@app.route("/chemin_result")
def chemin_result():

    parser = get_parser()

    if parser is None:
        return jsonify([])

    person1 = request.args.get("person1")
    person2 = request.args.get("person2")

    p1 = None
    p2 = None

    for indiv in parser.get_root_child_elements():

        if isinstance(
            indiv,
            IndividualElement
        ):

            prenom, nom = indiv.get_name()
            full = f"{prenom} {nom}"

            if full == person1:
                p1 = indiv

            if full == person2:
                p2 = indiv

    if p1 and p2:

        try:

            nodes = parser.display_relationship_path(
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

    q = request.args.get(
        "q",
        ""
    )

    personnes = []

    cursor = persons_collection.find(
        {
            "fullname": {
                "$regex": q,
                "$options": "i"
            }
        }
    ).limit(10)

    for doc in cursor:

        personnes.append(
            doc["fullname"]
        )

    return jsonify(personnes)


# ------------------------------------------------------------------
# Fiche personne
# ------------------------------------------------------------------

@app.route("/personne")
def personne():

    parser = get_parser()

    if parser is None:
        return "Veuillez charger un GEDCOM"

    nom_complet = request.args.get("nom")

    personne = None

    for indiv in parser.get_root_child_elements():

        if isinstance(
            indiv,
            IndividualElement
        ):

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

        parents = parser.get_parents(
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

        enfants = parser.get_enfants(
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
