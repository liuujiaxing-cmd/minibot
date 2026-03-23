from ..tools import tool
import os
import re
import json
import zipfile
import subprocess

def _valid_name(name: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_\-]*$", name or ""))

def _valid_python_identifier(name: str) -> bool:
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name or ""))

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _write(path: str, content: str) -> None:
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def _read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _append_to_skills_sh(block: str, label: str) -> str:
    block = (block or "").strip()
    if not block:
        return "Error: Empty bash entry."

    try:
        try:
            with open("skills.sh", "r", encoding="utf-8") as f:
                original = f.read()
        except FileNotFoundError:
            original = "#!/bin/bash\n"

        temp_file = "skills.temp.sh"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(original)
            f.write("\n\n")
            f.write(f"# Installed: {label}\n")
            f.write(block)
            f.write("\n")

        check = subprocess.run(["bash", "-n", temp_file], capture_output=True, text=True)
        if check.returncode != 0:
            os.remove(temp_file)
            return f"Error: bash syntax check failed.\nDetails: {check.stderr}"

        os.rename(temp_file, "skills.sh")
        return "ok"
    except Exception as e:
        return f"Error writing skills.sh: {str(e)}"

def _plugins_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")

@tool(name="scaffold_skill_pack", description="Create a shareable skill pack skeleton. Usage: scaffold_skill_pack(name='hello_skill', kind='python'|'bash', description='...', output_dir='.trae/skills_src')")
def scaffold_skill_pack(name: str, kind: str, description: str = "", output_dir: str = ".trae/skills_src"):
    kind = (kind or "").strip().lower()
    if kind not in {"python", "bash"}:
        return "Error: kind must be 'python' or 'bash'."

    if kind == "python":
        if not _valid_python_identifier(name):
            return "Error: Python skill name must be a valid identifier (letters/numbers/_)."
    else:
        if not _valid_name(name):
            return "Error: Bash skill name must use letters/numbers/_/- only."

    pack_dir = os.path.join(output_dir, name)
    _ensure_dir(pack_dir)

    if kind == "python":
        entry = f"{name}.py"
        tool_desc = description or f"{name} skill"
        entry_content = "\n".join([
            "from ..tools import tool",
            "",
            f"@tool(name={name!r}, description={tool_desc!r})",
            f"def {name}(text: str = ''):",
            "    return text or 'ok'",
            ""
        ])
    else:
        entry = "skill.sh"
        entry_content = "\n".join([
            f"function {name}() {{",
            "    echo \"ok\"",
            "}",
            ""
        ])

    manifest = {
        "name": name,
        "version": "0.1.0",
        "type": kind,
        "entry": entry,
        "description": description or "",
    }
    _write(os.path.join(pack_dir, "skillpack.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    skill_md = "\n".join([
        f"# {name}",
        "",
        description or "Skill description.",
        "",
        "## Install (GitHub)",
        f"- add_skill_from_git(repo='OWNER/REPO', skill_name='{name}', ref='main')",
        "",
        "## Usage",
        f"- If python: call tool `{name}` after restart.",
        f"- If bash: call execute_skill('{name}')",
        "",
        "## Files",
        "- skillpack.json",
        "- SKILL.md",
        f"- {entry}",
        ""
    ])
    _write(os.path.join(pack_dir, "SKILL.md"), skill_md)
    _write(os.path.join(pack_dir, entry), entry_content)

    return f"✅ Created skill pack at {pack_dir}."

@tool(name="pack_skill_pack", description="Zip a skill pack directory for sharing. Usage: pack_skill_pack(skill_dir='.trae/skills_src/hello_skill', out_zip='.trae/skillpacks/hello_skill.zip')")
def pack_skill_pack(skill_dir: str, out_zip: str = ""):
    if not skill_dir:
        return "Error: skill_dir is required."
    if not os.path.isdir(skill_dir):
        return f"Error: Not a directory: {skill_dir}"

    name = os.path.basename(os.path.abspath(skill_dir))
    out_zip = out_zip or os.path.join(".trae", "skillpacks", f"{name}.zip")
    _ensure_dir(os.path.dirname(out_zip))

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(skill_dir):
            for fn in files:
                abs_path = os.path.join(root, fn)
                rel_path = os.path.relpath(abs_path, start=skill_dir)
                z.write(abs_path, arcname=os.path.join(name, rel_path))

    return f"✅ Packed skill pack to {out_zip}."

@tool(name="install_skill_pack_from_path", description="Install a local skill pack directory (for testing/offline). Usage: install_skill_pack_from_path(skill_dir='.trae/skills_src/hello_skill')")
def install_skill_pack_from_path(skill_dir: str):
    if not skill_dir:
        return "Error: skill_dir is required."
    if not os.path.isdir(skill_dir):
        return f"Error: Not a directory: {skill_dir}"

    manifest_path = os.path.join(skill_dir, "skillpack.json")
    if not os.path.isfile(manifest_path):
        return "Error: skillpack.json not found in skill_dir."

    manifest = _read_json(manifest_path)
    name = (manifest.get("name") or "").strip()
    pack_type = (manifest.get("type") or "").strip().lower()
    entry = (manifest.get("entry") or "").strip()

    if pack_type not in {"python", "bash"}:
        return "Error: Invalid manifest type."
    if not entry:
        return "Error: Manifest entry is required."

    if pack_type == "python":
        if not _valid_python_identifier(name):
            return "Error: Python skill name must be a valid identifier."
    else:
        if not _valid_name(name):
            return "Error: Invalid manifest name."

    entry_path = os.path.join(skill_dir, entry)
    if not os.path.isfile(entry_path):
        return f"Error: Entry file not found: {entry_path}"

    with open(entry_path, "r", encoding="utf-8") as f:
        entry_text = f.read()

    skills_store = os.path.join(os.getcwd(), ".trae", "skills", name)
    _ensure_dir(skills_store)
    _write(os.path.join(skills_store, "skillpack.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for fn in ["SKILL.md", os.path.basename(entry)]:
        src = os.path.join(skill_dir, fn)
        if os.path.isfile(src):
            with open(src, "r", encoding="utf-8") as f:
                _write(os.path.join(skills_store, fn), f.read())

    if pack_type == "bash":
        r = _append_to_skills_sh(entry_text, f"local:{name}")
        if r != "ok":
            return r
        return f"✅ Installed bash skill '{name}' into skills.sh. Files saved under {skills_store}."

    _ensure_dir(_plugins_dir())
    plugin_path = os.path.join(_plugins_dir(), f"{name}.py")
    _write(plugin_path, entry_text)
    return f"✅ Installed python skill '{name}' to {plugin_path}. Restart Minibot to load it. Files saved under {skills_store}."

@tool(name="list_installed_skill_packs", description="List installed skill packs under .trae/skills/")
def list_installed_skill_packs():
    base = os.path.join(os.getcwd(), ".trae", "skills")
    if not os.path.isdir(base):
        return "No installed skill packs found."
    names = []
    for d in os.listdir(base):
        if os.path.isdir(os.path.join(base, d)):
            names.append(d)
    if not names:
        return "No installed skill packs found."
    names.sort()
    return "Installed skill packs: " + ", ".join(names)
