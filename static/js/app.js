async function rechercherPersonnes(inputId, boxId) {

    let query = document.getElementById(inputId).value;

    if (query.length < 2) return;

    let response = await fetch("/api/personnes?q=" + query);
    let data = await response.json();

    let box = document.getElementById(boxId);
    box.innerHTML = "";

    data.forEach(name => {

        let div = document.createElement("div");
        div.className = "suggestion";
        div.innerText = name;

        div.onclick = () => {
            document.getElementById(inputId).value = name;
            box.innerHTML = "";
        };

        box.appendChild(div);
    });
}


document.addEventListener("input", function(e) {

    if (e.target.id === "p1") {
        rechercherPersonnes("p1", "suggestions1");
    }

    if (e.target.id === "p2") {
        rechercherPersonnes("p2", "suggestions2");
    }
});