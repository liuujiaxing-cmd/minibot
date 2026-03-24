from ..tools import tool, reload_plugins
import os
import subprocess
import time
import hashlib

def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def _normalize_path(path: str) -> str:
    if not path:
        return ""
    p = os.path.expanduser(path)
    if os.path.isabs(p):
        return os.path.abspath(p)
    return os.path.abspath(os.path.join(_repo_root(), p))

def _is_allowed(path_abs: str) -> bool:
    root = _repo_root()
    if not path_abs.startswith(root + os.sep):
        return False

    rel = os.path.relpath(path_abs, root)
    allow_core = os.getenv("SELF_MODIFY_ALLOW_CORE", "0").strip().lower() in {"1", "true", "yes", "on"}
    if rel.startswith(os.path.join("minibot", "plugins") + os.sep):
        return True
    if rel == "skills.sh":
        return True
    if rel == os.path.join("minibot", "soul.txt"):
        return True
    if allow_core and (rel.startswith("minibot" + os.sep) or rel in {"main.py"}):
        return True
    return False

def _sha256(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

def _backup_path(path_abs: str) -> str:
    root = _repo_root()
    ts = time.strftime("%Y%m%d_%H%M%S")
    rel = os.path.relpath(path_abs, root)
    safe_rel = rel.replace(os.sep, "__")
    backup_dir = os.path.join(root, ".trae", "backups")
    os.makedirs(backup_dir, exist_ok=True)
    return os.path.join(backup_dir, f"{ts}__{safe_rel}.bak")

def _read_text(path_abs: str) -> str:
    with open(path_abs, "r", encoding="utf-8") as f:
        return f.read()

def _write_text(path_abs: str, content: str) -> None:
    os.makedirs(os.path.dirname(path_abs), exist_ok=True)
    with open(path_abs, "w", encoding="utf-8") as f:
        f.write(content)

def _verify(path_abs: str) -> tuple[bool, str]:
    if path_abs.endswith(".py"):
        r = subprocess.run(["python3", "-m", "py_compile", path_abs], capture_output=True, text=True)
        if r.returncode != 0:
            return False, (r.stderr or r.stdout or "py_compile failed").strip()
        return True, "ok"
    if os.path.basename(path_abs) == "skills.sh":
        r = subprocess.run(["bash", "-n", path_abs], capture_output=True, text=True)
        if r.returncode != 0:
            return False, (r.stderr or r.stdout or "bash -n failed").strip()
        return True, "ok"
    return True, "ok"

@tool(name="self_edit_file", description="Safely edit Minibot code with verification+rollback. Default allows minibot/plugins, skills.sh, minibot/soul.txt. Usage: self_edit_file(path='minibot/plugins/x.py', new_content='...', expected_sha256='optional')")
def self_edit_file(path: str, new_content: str, expected_sha256: str = ""):
    path_abs = _normalize_path(path)
    if not path_abs:
        return "Error: path is required."
    if not _is_allowed(path_abs):
        return "Error: path not allowed. Only minibot/plugins/*, skills.sh, minibot/soul.txt are allowed by default. Set SELF_MODIFY_ALLOW_CORE=1 to allow core edits."

    existed = os.path.exists(path_abs)
    old = ""
    if existed:
        try:
            old = _read_text(path_abs)
        except Exception as e:
            return f"Error: cannot read original file: {str(e)}"

    if expected_sha256:
        if _sha256(old) != expected_sha256.strip():
            return "Error: file changed since last read (sha256 mismatch). Re-read and try again."

    backup = ""
    try:
        backup = _backup_path(path_abs)
        if existed:
            _write_text(backup, old)

        _write_text(path_abs, new_content or "")
        ok, detail = _verify(path_abs)
        if not ok:
            if existed:
                _write_text(path_abs, old)
            else:
                try:
                    os.remove(path_abs)
                except Exception:
                    pass
            return f"Error: verification failed; rolled back. Details: {detail}"

        return f"✅ Updated {path_abs}. Backup: {backup if existed else '(none, new file)'}"
    except Exception as e:
        try:
            if existed:
                _write_text(path_abs, old)
        except Exception:
            pass
        return f"Error editing file: {str(e)}"

@tool(name="self_reload_plugins", description="Reload all plugins and refresh tool registry in current process.")
def self_reload_plugins():
    loaded = reload_plugins()
    return "✅ Plugins reloaded: " + ", ".join(loaded)

