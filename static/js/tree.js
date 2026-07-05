async function chercher() {
    let p1 = document.getElementById("p1").value;
    let p2 = document.getElementById("p2").value;

    let response = await fetch(`/chemin_result?person1=${encodeURIComponent(p1)}&person2=${encodeURIComponent(p2)}`);
    let data = await response.json();
    
    renderTree(data);
}

function renderTree(data) {
    let container = document.getElementById("tree");
    container.innerHTML = "";
    
    data.forEach(node => {
        let div = document.createElement("div");
        div.className = "node";
        div.innerText = node.name;
        div.style.marginLeft = (node.level * 30) + "px"; // Indentation visuelle
        container.appendChild(div);
    });
}