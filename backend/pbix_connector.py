import os, json, subprocess, glob

CONFIG_PATH = os.path.expanduser("~/.albert_pbi/config.json")

# ----------------- API KEY -----------------
def save_api_key(key):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"api_key": key}, f)

def load_api_key():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f).get("api_key","")
    return ""

# ----------------- PBIX MODEL -----------------
def find_running_pbix_port():
    base = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces")
    if not os.path.exists(base):
        return None
    folders = glob.glob(os.path.join(base, "*"))
    for f in folders:
        port_file = os.path.join(f, "msmdsrv.port.txt")
        if os.path.exists(port_file):
            with open(port_file) as pf:
                port = pf.read().strip()
                return f"localhost:{port}"
    return None

def get_pbix_metadata():
    port = find_running_pbix_port()
    if not port:
        return []

    dll_path = os.path.abspath("../pbix_reader/PBIXReader.dll")
    if not os.path.exists(dll_path):
        return []

    try:
        result = subprocess.run(
            ["dotnet", "exec", dll_path, port, "Model"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return []
        return json.loads(result.stdout)
    except Exception:
        return []
