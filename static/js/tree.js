async function chercher() {

    let p1 =
        document.getElementById("p1").value;

    let p2 =
        document.getElementById("p2").value;

    if (!p1 || !p2) {

        alert(
            "Choisissez deux personnes"
        );

        return;
    }

    renderTree([
        {
            name: p1,
            type: "root",
            level: 0
        },
        {
            name: "↕",
            type: "node",
            level: 1
        },
        {
            name: p2,
            type: "root",
            level: 2
        }
    ]);
}

function renderTree(data) {

    let container =
        document.getElementById(
            "tree"
        );

    container.innerHTML = "";

    data.forEach(node => {

        let div =
            document.createElement(
                "div"
            );

        div.className =
            node.type === "root"
            ? "root"
            : "node";

        div.innerText =
            node.name;

        div.style.marginLeft =
            (node.level * 60) + "px";

        container.appendChild(div);
    });
}