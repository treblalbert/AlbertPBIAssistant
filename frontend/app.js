let modelData = [];
let selectedTables = new Set();

async function saveKey(){
    const key = document.getElementById("apikey").value;
    if(!key){
        document.getElementById("save-status").textContent = "Enter a key first!";
        return;
    }
    const res = await fetch("/save-key", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({key})
    });
    const data = await res.json();
    document.getElementById("save-status").textContent = data.message || "Key saved!";
}

async function loadKeyFile(){
    const file = document.getElementById("keyfile").files[0];
    if(!file) return;
    const text = await file.text();
    const res = await fetch("/save-key", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({key:text.trim()})
    });
    const data = await res.json();
    document.getElementById("save-status").textContent = data.message || "Key loaded from file!";
}

async function loadModel(){
    const res = await fetch("/get-model");
    const data = await res.json();
    if(data.status !== "ok" || !data.model || data.model.length === 0){
        document.getElementById("model-status").textContent = "No tables found or PBIX not running.";
        return;
    }

    modelData = data.model;
    const ul = document.getElementById("tables");
    ul.innerHTML = "";
    data.model.forEach(table => {
        const li = document.createElement("li");
        li.textContent = table.Name;
        li.onclick = () => {
            if(selectedTables.has(table.Name)){
                selectedTables.delete(table.Name);
                li.classList.remove("selected");
            } else {
                selectedTables.add(table.Name);
                li.classList.add("selected");
            }
        }
        ul.appendChild(li);

        const colUl = document.createElement("ul");
        table.Columns.forEach(col => {
            const colLi = document.createElement("li");
            colLi.textContent = col;
            colLi.style.paddingLeft = "20px";
            colUl.appendChild(colLi);
        });
        li.appendChild(colUl);
    });

    document.getElementById("model-status").textContent = "Model loaded successfully! Select tables.";
}

async function ask(){
    const prompt = document.getElementById("prompt").value;
    if(!prompt){
        alert("Enter a prompt first!");
        return;
    }

    const selectedData = modelData.filter(t => selectedTables.has(t.Name));
    if(selectedData.length === 0){
        alert("Select at least one table!");
        return;
    }

    const res = await fetch("/ask", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({prompt, selected_data: selectedData})
    });
    const data = await res.json();
    document.getElementById("response").textContent = data.answer;
}
