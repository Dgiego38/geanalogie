from flask import Flask, render_template, request, jsonify
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

import tempfile
import requests
import os

app = Flask(__name__)

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


# ------------------------------------------------------------------
# GEDCOM chargé par l'utilisateur
# ------------------------------------------------------------------

gedcom_parser = None

def construire_base_mongodb():

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
        return gedcom_parser


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
    return render_template(
        "upload.html"
    )   


@app.route(
    "/process_blob",
    methods=["POST"]
)
def process_blob():

    global gedcom_parser

    data = request.get_json()

    blob_url = data["url"]

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".ged"
    )

    r = requests.get(blob_url)

    with open(
        temp.name,
        "wb"
    ) as f:

        f.write(
            r.content
        )

    gedcom_parser = Parser()

    gedcom_parser.parse_file(
        temp.name,
        False
    )

    construire_base_mongodb()

    os.remove(
        temp.name
    )

    return jsonify({
        "success": True
    })

    @app.route("/menu")
    def accueil():
        return render_template(
            "index.html"
        )

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

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
