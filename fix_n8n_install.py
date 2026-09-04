"""
================================================================================
  🛠️ n8n Global Fix & Clean Installer
================================================================================
"""

import os
import sys
import shutil
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

appdata = os.environ.get("APPDATA", "")
npm_dir = os.path.join(appdata, "npm")
n8n_module_dir = os.path.join(npm_dir, "node_modules", "n8n")

print("1. Cleaning old corrupted n8n folders...")
if os.path.exists(n8n_module_dir):
    try:
        shutil.rmtree(n8n_module_dir, ignore_errors=True)
        print(f"Removed: {n8n_module_dir}")
    except Exception as e:
        print(f"Cleanup note: {e}")

# Remove n8n binary files in npm folder
if os.path.exists(npm_dir):
    for item in os.listdir(npm_dir):
        if item.startswith("n8n"):
            item_path = os.path.join(npm_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)
                print(f"Removed npm link: {item}")
            except Exception:
                pass

print("\n2. Running fresh clean npm install for n8n...")
cmd = ["npm.cmd" if os.name == "nt" else "npm", "install", "-g", "n8n", "--ignore-scripts", "--no-audit", "--no-fund"]
print("Executing:", " ".join(cmd))

p = subprocess.run(cmd, capture_output=True, text=True)
print("Return Code:", p.returncode)
if p.stdout:
    print("STDOUT:\n", p.stdout[-600:])
if p.stderr:
    print("STDERR:\n", p.stderr[-600:])

print("\n3. Testing n8n version command...")
try:
    p_ver = subprocess.run(["n8n.cmd" if os.name == "nt" else "n8n", "--version"], capture_output=True, text=True, timeout=10)
    print("n8n Version Output:", p_ver.stdout.strip() or p_ver.stderr.strip())
except Exception as ex:
    print("Version check exception:", ex)
