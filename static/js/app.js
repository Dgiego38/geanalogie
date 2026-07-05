// Récupération du sessionId depuis l'URL
const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get('sessionId');

// Fonction générique pour gérer les suggestions
async function setupAutocomplete(inputId, suggestionId) {
    const input = document.getElementById(inputId);
    const suggestionBox = document.getElementById(suggestionId);

    input.addEventListener('input', async (e) => {
        const query = e.target.value;
        if (query.length < 2) {
            suggestionBox.innerHTML = "";
            return;
        }

        // Appel API vers app.py
        const response = await fetch(`/api/personnes?q=${encodeURIComponent(query)}&sessionId=${sessionId}`);
        const data = await response.json();

        // Affichage des suggestions
        suggestionBox.innerHTML = "";
        data.forEach(name => {
            const div = document.createElement("div");
            div.className = "suggestion";
            div.innerText = name;
            div.onclick = () => {
                input.value = name;
                suggestionBox.innerHTML = "";
            };
            suggestionBox.appendChild(div);
        });
    });
}

// Initialisation pour les deux champs
setupAutocomplete('p1', 'suggestions1');
setupAutocomplete('p2', 'suggestions2');