"""
================================================================================
  🤗 1-Click Push to Hugging Face Spaces via Dulwich
================================================================================
"""

import os
import sys
import shutil
import time
from dulwich.repo import Repo
from dulwich.objects import Blob, Commit
from dulwich.index import index_entry_from_stat
from dulwich.porcelain import push

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = r"c:\Users\SURAJ\Documents\Coding space\omnidim_hub"

ignore_dirs = {"__pycache__", ".git", ".gemini", ".idea", ".vscode", "venv"}
ignore_exts = {".pyc", ".log", ".tmp", ".pyd", ".bin"}
ignore_files = {
    ".env", ".encrypted_vault.bin", ".vault_salt.bin", ".vault_hash.bin",
    "push_to_github.py", "push_to_github_clean.py", "force_git_push.py",
    "manage_justrunmy_app.py", "push_to_justrunmy_app.py", "update_profile_readme.py",
    "push_to_huggingface.py"
}

def push_to_hf(hf_token):
    print("=" * 70)
    print("  🤗 Staging & Pushing Clean Source to Hugging Face Space")
    print("=" * 70)

    hf_remote = f"https://cyberexpert29:{hf_token}@huggingface.co/spaces/cyberexpert29/cybercalling-hub.git"

    # Re-init fresh git repo
    git_dir = os.path.join(BASE_DIR, ".git")
    if os.path.exists(git_dir):
        try:
            shutil.rmtree(git_dir)
        except Exception:
            pass

    repo = Repo.init(BASE_DIR)
    index = repo.open_index()

    count = 0
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
        for f in files:
            ext = os.path.splitext(f)[1]
            if f in ignore_files or ext in ignore_exts or f.endswith(".zip"):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, BASE_DIR).replace("\\", "/")
            
            with open(full_path, "rb") as fp:
                data = fp.read()
                blob = Blob.from_string(data)
                repo.object_store.add_object(blob)
                st = os.stat(full_path)
                index[rel_path.encode("utf-8")] = index_entry_from_stat(st, blob.id, 0)
                count += 1

    index.write()
    tree_id = index.commit(repo.object_store)
    print(f"Staged {count} files to clean tree {tree_id.decode() if isinstance(tree_id, bytes) else tree_id}")

    # Create Commit
    c = Commit()
    c.tree = tree_id
    c.parents = []

    author = b"Dark Angel Core <core@darkangel.telecom>"
    msg = b"Deploy 24/7 Dark Angel Voice AI Telecom Core System"

    c.author = author
    c.committer = author
    c.author_time = int(time.time())
    c.author_timezone = 0
    c.commit_time = int(time.time())
    c.commit_timezone = 0
    c.message = msg

    repo.object_store.add_object(c)
    repo.refs[b"refs/heads/main"] = c.id
    repo.refs[b"HEAD"] = c.id
    print(f"Created Clean Commit: {c.id.decode() if isinstance(c.id, bytes) else c.id}")

    # Push to Hugging Face
    print("Pushing to Hugging Face (refs/heads/main)...")
    try:
        push(repo, hf_remote, refspecs=[b"refs/heads/main:refs/heads/main"], force=True)
        print("\n🎉 SUCCESS: All code has been pushed cleanly to Hugging Face Space!")
    except Exception as e:
        print("Push Result:", e)

if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else os.getenv("HF_TOKEN", "")
    if not token:
        print("Please provide your Hugging Face Access Token.")
    else:
        push_to_hf(token)
