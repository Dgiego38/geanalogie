async function chercher() {
    let p1 = document.getElementById("p1").value;
    let p2 = document.getElementById("p2").value;

    // Utilisation du sessionId
    let response = await fetch(`/chemin_result?sessionId=${sessionId}&person1=${encodeURIComponent(p1)}&person2=${encodeURIComponent(p2)}`);
    
    if (!response.ok) return console.error("Erreur serveur");
    
    let data = await response.json();
    renderTree(data);
}

function renderTree(data) {
    let container = document.getElementById("tree");
    container.innerHTML = "";
    data.forEach(node => {
        let div = document.createElement("div");
        div.className = (node.type === "root") ? "root" : "node";
        div.innerText = node.name;
        div.style.marginLeft = (node.level * 60) + "px";
        container.appendChild(div);
    });
}