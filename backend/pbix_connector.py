import os
import json
import subprocess
import glob

CONFIG_PATH = os.path.expanduser("~/.albert_pbi/config.json")

# ----------------- API KEY -----------------
def save_api_key(key):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"api_key": key}, f)

def load_api_key():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f).get("api_key", "")
    return ""

# ----------------- PBIX MODEL -----------------
def find_running_pbix_port():
    """Find the port of a running Power BI Desktop instance"""
    base = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces")
    
    print(f"[DEBUG] Looking for Power BI workspaces at: {base}")
    
    if not os.path.exists(base):
        print(f"[ERROR] Base directory does not exist: {base}")
        return None
    
    folders = glob.glob(os.path.join(base, "*"))
    print(f"[DEBUG] Found {len(folders)} workspace folders")
    
    for folder in folders:
        port_file = os.path.join(folder, "msmdsrv.port.txt")
        print(f"[DEBUG] Checking: {port_file}")
        
        if os.path.exists(port_file):
            try:
                with open(port_file) as pf:
                    port = pf.read().strip()
                    connection_string = f"localhost:{port}"
                    print(f"[SUCCESS] Found Power BI instance at: {connection_string}")
                    return connection_string
            except Exception as e:
                print(f"[ERROR] Could not read port file: {e}")
                continue
    
    print("[ERROR] No running Power BI Desktop instance found")
    return None

def get_pbix_metadata():
    """Get tables, columns, and measures from Power BI Desktop"""
    port = find_running_pbix_port()
    if not port:
        print("[ERROR] No Power BI port found")
        return []

    # Find the DLL - try multiple locations
    possible_dll_paths = [
        os.path.abspath("../pbix_reader/PBIXReader.dll"),
        os.path.abspath("./pbix_reader/PBIXReader.dll"),
        os.path.join(os.path.dirname(__file__), "../pbix_reader/PBIXReader.dll"),
        os.path.join(os.path.dirname(__file__), "pbix_reader/PBIXReader.dll"),
    ]
    
    dll_path = None
    for path in possible_dll_paths:
        print(f"[DEBUG] Checking for DLL at: {path}")
        if os.path.exists(path):
            dll_path = path
            print(f"[SUCCESS] Found DLL at: {dll_path}")
            break
    
    if not dll_path:
        print("[ERROR] PBIXReader.dll not found in any expected location")
        print("[INFO] Expected locations:")
        for path in possible_dll_paths:
            print(f"  - {path}")
        return []

    try:
        print(f"[DEBUG] Running: dotnet exec {dll_path} {port} Model")
        result = subprocess.run(
            ["dotnet", "exec", dll_path, port, "Model"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"[DEBUG] Return code: {result.returncode}")
        print(f"[DEBUG] STDOUT: {result.stdout[:500]}")  # First 500 chars
        print(f"[DEBUG] STDERR: {result.stderr[:500]}")  # First 500 chars
        
        if result.returncode != 0:
            print(f"[ERROR] DLL execution failed with code {result.returncode}")
            print(f"[ERROR] Error output: {result.stderr}")
            return []
        
        if not result.stdout.strip():
            print("[ERROR] DLL returned empty output")
            return []
        
        data = json.loads(result.stdout)
        print(f"[SUCCESS] Loaded {len(data)} tables from Power BI")
        return data
        
    except subprocess.TimeoutExpired:
        print("[ERROR] DLL execution timed out after 10 seconds")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON from DLL: {e}")
        print(f"[ERROR] Raw output: {result.stdout}")
        return []
    except FileNotFoundError:
        print("[ERROR] 'dotnet' command not found. Is .NET SDK installed?")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}: {e}")
        return []


# Test function you can run manually
if __name__ == "__main__":
    print("=== Testing Power BI Connection ===\n")
    port = find_running_pbix_port()
    if port:
        print(f"\n✅ Power BI is running at: {port}")
        print("\n=== Attempting to read model ===\n")
        tables = get_pbix_metadata()
        if tables:
            print(f"\n✅ Successfully loaded {len(tables)} tables:")
            for table in tables:
                print(f"  - {table['Name']} ({len(table['Columns'])} columns)")
        else:
            print("\n❌ Failed to load tables")
    else:
        print("\n❌ Power BI Desktop is not running or no file is open")