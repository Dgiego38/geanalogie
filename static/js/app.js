// Utilise window.sessionId défini dans chemin.html
async function setupAutocomplete(inputId, suggestionId) {
    const input = document.getElementById(inputId);
    const suggestionBox = document.getElementById(suggestionId);
    input.addEventListener('input', async (e) => {
        const query = e.target.value;
        if (query.length < 2) { suggestionBox.innerHTML = ""; return; }
        const response = await fetch(`/api/personnes?q=${encodeURIComponent(query)}&sessionId=${window.sessionId}`);
        const data = await response.json();
        suggestionBox.innerHTML = "";
        data.forEach(name => {
            const div = document.createElement("div");
            div.className = "suggestion";
            div.innerText = name;
            div.onclick = () => { input.value = name; suggestionBox.innerHTML = ""; };
            suggestionBox.appendChild(div);
        });
    });
}
setupAutocomplete('p1', 'suggestions1');
setupAutocomplete('p2', 'suggestions2');