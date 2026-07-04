let personnes = [];

/* -------------------------- */
/* Lecture GEDCOM depuis DB   */
/* -------------------------- */

async function chargerGedcom() {

    return new Promise((resolve, reject) => {

        const request =
            indexedDB.open(
                "GenealogieDB",
                1
            );

        request.onsuccess =
            function(event){

                const db =
                    event.target.result;

                const tx =
                    db.transaction(
                        ["files"],
                        "readonly"
                    );

                const store =
                    tx.objectStore(
                        "files"
                    );

                const getReq =
                    store.get(
                        "gedcom"
                    );

                getReq.onsuccess =
                    async function(){

                        const file =
                            getReq.result;

                        if(!file){

                            alert(
                                "Aucun GEDCOM chargé"
                            );

                            window.location.href =
                                "/";

                            return;
                        }

                        const text =
                            await file.text();

                        lirePersonnes(text);

                        resolve();
                    };

                getReq.onerror =
                    () => reject();
            };
    });
}

/* -------------------------- */
/* Extraction des noms GEDCOM */
/* -------------------------- */

function lirePersonnes(text){

    personnes = [];

    const lignes =
        text.split("\n");

    let prenom = "";
    let nom = "";

    for(const ligne of lignes){

        if(
            ligne.includes(" NAME ")
        ){

            const match =
                ligne.match(
                    /NAME\s+(.*?)\s*\/(.*?)\//
                );

            if(match){

                prenom =
                    match[1].trim();

                nom =
                    match[2].trim();

                personnes.push(
                    prenom +
                    " " +
                    nom
                );
            }
        }
    }

    console.log(
        personnes.length +
        " personnes chargées"
    );
}

/* -------------------------- */
/* Suggestions                */
/* -------------------------- */

function rechercherPersonnes(
    inputId,
    boxId
){

    const query =
        document
        .getElementById(
            inputId
        )
        .value
        .toLowerCase();

    const box =
        document.getElementById(
            boxId
        );

    box.innerHTML = "";

    if(query.length < 2){
        return;
    }

    const resultat =
        personnes
        .filter(
            p =>
            p.toLowerCase()
            .includes(query)
        )
        .slice(0,10);

    resultat.forEach(name => {

        const div =
            document.createElement(
                "div"
            );

        div.className =
            "suggestion";

        div.innerText =
            name;

        div.onclick = () => {

            document
            .getElementById(
                inputId
            )
            .value =
                name;

            box.innerHTML = "";
        };

        box.appendChild(div);
    });
}

/* -------------------------- */
/* Events                     */
/* -------------------------- */

document.addEventListener(
    "input",
    function(e){

        if(
            e.target.id === "p1"
        ){
            rechercherPersonnes(
                "p1",
                "suggestions1"
            );
        }

        if(
            e.target.id === "p2"
        ){
            rechercherPersonnes(
                "p2",
                "suggestions2"
            );
        }
    }
);

chargerGedcom();