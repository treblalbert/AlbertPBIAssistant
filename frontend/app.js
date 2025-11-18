const API_BASE = "http://localhost:8000";

let modelData = [];
let selectedTables = new Set();

// Helper to show status messages
function showStatus(elementId, message, isError = false) {
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.style.color = isError ? "#ef4444" : "#10b981";
    el.style.fontWeight = "bold";
}

async function saveKey() {
    const key = document.getElementById("apikey").value.trim();
    if (!key) {
        showStatus("save-status", "⚠️ Enter a key first!", true);
        return;
    }
    
    try {
        showStatus("save-status", "⏳ Saving...");
        const res = await fetch(`${API_BASE}/save-key`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({key})
        });
        
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }
        
        const data = await res.json();
        showStatus("save-status", `✓ ${data.message || "Key saved!"}`);
    } catch (error) {
        showStatus("save-status", `✗ Error: ${error.message}`, true);
        console.error("Save key error:", error);
    }
}

async function loadKeyFile() {
    const fileInput = document.getElementById("keyfile");
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus("save-status", "⚠️ Select a file first!", true);
        return;
    }
    
    try {
        showStatus("save-status", "⏳ Loading from file...");
        const text = await file.text();
        const key = text.trim();
        
        if (!key) {
            throw new Error("File is empty");
        }
        
        const res = await fetch(`${API_BASE}/save-key`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({key})
        });
        
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }
        
        const data = await res.json();
        showStatus("save-status", `✓ ${data.message || "Key loaded from file!"}`);
        
        // Also show the key in the input field (masked)
        document.getElementById("apikey").value = key;
    } catch (error) {
        showStatus("save-status", `✗ Error: ${error.message}`, true);
        console.error("Load key file error:", error);
    }
}

async function loadModel() {
    try {
        showStatus("model-status", "⏳ Loading Power BI model...");
        
        const res = await fetch(`${API_BASE}/get-model`);
        
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }
        
        const data = await res.json();
        
        if (data.status !== "ok" || !data.model || data.model.length === 0) {
            showStatus("model-status", "⚠️ No tables found. Is Power BI Desktop running with a file open?", true);
            return;
        }

        modelData = data.model;
        selectedTables.clear();
        
        const ul = document.getElementById("tables");
        ul.innerHTML = "";
        
        data.model.forEach(table => {
            const li = document.createElement("li");
            li.className = "table-item";
            li.innerHTML = `<strong>${table.Name}</strong> <span class="table-count">(${table.Columns.length} cols)</span>`;
            
            li.onclick = () => {
                if (selectedTables.has(table.Name)) {
                    selectedTables.delete(table.Name);
                    li.classList.remove("selected");
                } else {
                    selectedTables.add(table.Name);
                    li.classList.add("selected");
                }
                updateSelectionCount();
            };
            
            ul.appendChild(li);

            // Show columns as sub-list
            const colUl = document.createElement("ul");
            colUl.className = "column-list";
            table.Columns.forEach(col => {
                const colLi = document.createElement("li");
                colLi.textContent = col;
                colUl.appendChild(colLi);
            });
            
            // Show measures if any
            if (table.Measures && table.Measures.length > 0) {
                const measureLi = document.createElement("li");
                measureLi.style.color = "#fbbf24";
                measureLi.innerHTML = `<em>Measures: ${table.Measures.join(", ")}</em>`;
                colUl.appendChild(measureLi);
            }
            
            li.appendChild(colUl);
        });

        showStatus("model-status", `✓ Loaded ${data.model.length} tables! Click to select.`);
    } catch (error) {
        showStatus("model-status", `✗ Error: ${error.message}. Is backend running on port 8000?`, true);
        console.error("Load model error:", error);
    }
}

function updateSelectionCount() {
    const count = selectedTables.size;
    const statusEl = document.getElementById("model-status");
    if (count > 0) {
        showStatus("model-status", `✓ ${count} table${count > 1 ? 's' : ''} selected`);
    }
}

async function ask() {
    const prompt = document.getElementById("prompt").value.trim();
    
    if (!prompt) {
        document.getElementById("response").textContent = "⚠️ Enter a prompt first!";
        return;
    }

    const selectedData = modelData.filter(t => selectedTables.has(t.Name));
    
    if (selectedData.length === 0) {
        document.getElementById("response").textContent = "⚠️ Select at least one table first!";
        return;
    }

    try {
        document.getElementById("response").textContent = "⏳ Asking OpenAI...";
        
        const res = await fetch(`${API_BASE}/ask`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                prompt, 
                selected_data: selectedData
            })
        });
        
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }
        
        const data = await res.json();
        document.getElementById("response").textContent = data.answer || "No response from API";
    } catch (error) {
        document.getElementById("response").textContent = `✗ Error: ${error.message}\n\nMake sure:\n- Backend is running\n- API key is saved\n- Power BI is open`;
        console.error("Ask error:", error);
    }
}

// Load saved key on startup
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const res = await fetch(`${API_BASE}/load-key`);
        if (res.ok) {
            const data = await res.json();
            if (data.status === "ok" && data.key) {
                document.getElementById("apikey").value = data.key;
                showStatus("save-status", "✓ API key loaded from config");
            }
        }
    } catch (error) {
        showStatus("save-status", "⚠️ Backend not connected", true);
    }
});