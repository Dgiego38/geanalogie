async function chercher() {
    let p1 = document.getElementById("p1").value;
    let p2 = document.getElementById("p2").value;

    if (!p1 || !p2) return alert("Veuillez remplir les deux noms");

    // Appel à votre backend
    let response = await fetch(`/chemin_result?sessionId=${sessionId}&person1=${encodeURIComponent(p1)}&person2=${encodeURIComponent(p2)}`);
    
    if (!response.ok) return console.error("Erreur lors de la récupération des données");
    
    let data = await response.json();
    
    // On lance le rendu
    renderTree(data);
}

function renderTree(data) {
    const container = document.getElementById("tree");
    container.innerHTML = ""; // Vider le conteneur

    // Vérification de sécurité
    if (!data) return;

    // Création du conteneur racine de l'arbre
    const rootUl = document.createElement("ul");
    rootUl.className = "genealogy-tree";
    
    // Fonction récursive pour construire les branches
    function createNode(person) {
        const li = document.createElement("li");
        
        // Création de la carte (box) de la personne
        const card = document.createElement("div");
        card.className = "person-card";
        card.innerHTML = `
            <div class="avatar">👤</div>
            <div class="info">
                <strong>${person.name}</strong><br>
                <small>${person.dates || ""}</small>
            </div>
        `;
        li.appendChild(card);

        // Si la personne a des enfants/parents (en fonction de votre logique)
        // On crée une sous-liste (<ul>) pour les afficher
        if (person.children && person.children.length > 0) {
            const ul = document.createElement("ul");
            person.children.forEach(child => {
                ul.appendChild(createNode(child));
            });
            li.appendChild(ul);
        }
        return li;
    }

    // Lancer la construction
    rootUl.appendChild(createNode(data));
    container.appendChild(rootUl);
}