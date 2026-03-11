from ..tools import tool
import requests
import os
import re
import subprocess

@tool(name="add_skill_from_git", description="Install a skill from a GitHub repository (like `npx skills add`). Usage: add_skill_from_git(repo='vercel-labs/agent-skills', skill_name='react-best-practices')")
def add_skill_from_git(repo: str, skill_name: str):
    """
    Fetches the `SKILL.md` or relevant files from a GitHub repository.
    Example: `vercel-labs/agent-skills` -> `skills/react-best-practices/SKILL.md`
    """
    
    # Construct the raw GitHub URL for SKILL.md
    # Assuming standard structure: https://raw.githubusercontent.com/<owner>/<repo>/main/skills/<skill_name>/SKILL.md
    base_url = f"https://raw.githubusercontent.com/{repo}/main/skills/{skill_name}/SKILL.md"
    
    try:
        response = requests.get(base_url)
        if response.status_code != 200:
            # Try without the 'skills/' prefix if it fails
            base_url = f"https://raw.githubusercontent.com/{repo}/main/{skill_name}/SKILL.md"
            response = requests.get(base_url)
            if response.status_code != 200:
                return f"Failed to fetch skill '{skill_name}' from '{repo}'. Check the repository and skill name."
        
        skill_content = response.text
        
        # Save locally to .trae/skills/ or minibot/skills/
        # Let's save it to a dedicated directory for downloaded skills
        skills_dir = os.path.join(os.getcwd(), ".trae", "skills", skill_name)
        os.makedirs(skills_dir, exist_ok=True)
        
        skill_file = os.path.join(skills_dir, "SKILL.md")
        with open(skill_file, "w") as f:
            f.write(skill_content)
            
        return f"✅ Skill '{skill_name}' installed successfully to {skill_file}. Minibot can now reference this skill."
        
    except Exception as e:
        return f"Error installing skill from git: {str(e)}"

# Mock remote skills repository (since we don't have a real website yet)
# In production, this would be a real URL like "https://minibot-skills.com/api/skills"
MOCK_REMOTE_SKILLS = {
    "weather_check": r"""
function weather_check() {
    curl -s "wttr.in/${1:-Beijing}?format=3"
}
""",
    "joke_generator": r"""
function joke_generator() {
    curl -s https://icanhazdadjoke.com/ -H "Accept: text/plain"
}
""",
    "disk_usage": r"""
function disk_usage() {
    df -h | grep -vE '^Filesystem|tmpfs|cdrom'
}
""",
    "git_status_check": r"""
function git_status_check() {
    if [ -d .git ]; then
        git status -s
    else
        echo "Not a git repository."
    fi
}
""",
    "check_battery": r"""
function check_battery() {
    pmset -g batt
}
""",
    "get_public_ip": r"""
function get_public_ip() {
    curl -s ifconfig.me
}
""",
    "list_top_processes": r"""
function list_top_processes() {
    ps aux | head -n 6
}
""",
    "whoami_info": r"""
function whoami_info() {
    echo "User: $(whoami)"
    echo "ID: $(id -u)"
    echo "Groups: $(groups)"
}
""",
    "get_top_news": r"""
function get_top_news() {
    # Fetches top headlines from BBC News RSS
    echo "--- Latest World News (BBC) ---"
    curl -s "http://feeds.bbci.co.uk/news/world/rss.xml" | grep -o '<title><!\[CDATA\[[^]]*\]\]></title>' | sed 's/<title><!\[CDATA\[//;s/\]\]><\/title>//' | head -n 10
}
""",
    "get_china_news": r"""
function get_china_news() {
    # Fetches top headlines from Google News (China)
    # Note: Requires network access to google.com
    echo "--- Latest China News (Google) ---"
    curl -s "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans" | grep -o '<title>[^<]*</title>' | sed 's/<title>//;s/<\/title>//' | grep -v "Google 新闻" | head -n 10
}
"""
}

@tool(name="install_skill", description="Download and install a skill from the remote repository to local skills.sh. Usage: install_skill(skill_name='weather_check')")
def install_skill(skill_name: str):
    """Download a skill function and append to skills.sh."""
    if skill_name not in MOCK_REMOTE_SKILLS:
        return f"Skill '{skill_name}' not found in the repository. Use find_skills to see available skills."
    
    skill_code = MOCK_REMOTE_SKILLS[skill_name]
    
    try:
        # Check if already installed
        try:
            with open("skills.sh", "r") as f:
                if f"function {skill_name}()" in f.read():
                    return f"Skill '{skill_name}' is already installed."
        except FileNotFoundError:
            pass
        
        # Append to file
        with open("skills.sh", "a") as f:
            f.write(f"\n# Installed from remote: {skill_name}\n{skill_code}\n")
            
        return f"Successfully installed skill: {skill_name}. You can now use execute_skill('{skill_name}')."
    except Exception as e:
        return f"Error installing skill: {str(e)}"

@tool(name="list_local_skills", description="List locally installed bash skills in skills.sh.")
def list_local_skills():
    """Parse skills.sh to find function names."""
    try:
        with open("skills.sh", "r") as f:
            content = f.read()
        
        # Regex to find function definitions like `function name() {` or `name() {`
        functions = re.findall(r'function\s+(\w+)\s*\(|^\s*(\w+)\s*\(\)\s*\{', content, re.MULTILINE)
        
        # Flatten the list of tuples from findall
        skill_names = [f[0] or f[1] for f in functions if f[0] or f[1]]
        
        if not skill_names:
            return "No local skills found."
        
        return "Locally installed skills: " + ", ".join(skill_names)
    except FileNotFoundError:
        return "skills.sh not found."
    except Exception as e:
        return f"Error listing skills: {str(e)}"

@tool(name="find_local_skills", description="Find/Search for local bash skills by keyword. Usage: find_local_skills(keyword='battery')")
def find_local_skills(keyword: str):
    """Search for skills in skills.sh using the embedded find_skills bash function."""
    # This uses the bash function 'find_skills' we added to skills.sh
    return execute_skill("find_skills", keyword)

@tool(name="execute_skill", description="Execute a bash function from skills.sh. Usage: execute_skill(skill_name='get_system_info', args='optional_arg')")
def execute_skill(skill_name: str, args: str = ""):
    """Execute a specific function from skills.sh."""
    try:
        # Import SafetyChecker here or rely on the agent to do it. 
        # For tool robustness, let's do a basic check here.
        if ";" in skill_name or "|" in skill_name or ";" in args or "|" in args:
             return "Security Error: Invalid characters in skill name or args."
        
        # Check if skills.sh is valid first
        check_syntax = subprocess.run(
            ["bash", "-n", "skills.sh"],
            capture_output=True,
            text=True
        )
        if check_syntax.returncode != 0:
            return f"CRITICAL ERROR: skills.sh has syntax errors and cannot be sourced. Please use 'add_skill' to fix it or manually edit the file.\nDetails: {check_syntax.stderr}"
        
        # Only allow whitelisted skills for safety (Example policy)
        # In a real app, you might want to allow all skills in skills.sh but be strict on args.
        
        command = f"source ./skills.sh && {skill_name} \"{args}\""
        
        result = subprocess.run(
            ["bash", "-c", command],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return f"Skill execution failed: {result.stderr}"
        
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Skill execution timed out."
    except Exception as e:
        return f"Error executing skill: {str(e)}"

@tool(name="add_skill", description="Add a new bash function to skills.sh. Usage: add_skill(name='hello', code='echo Hello World')")
def add_skill(name: str, code: str):
    """Append a new function to skills.sh."""
    try:
        # Basic validation
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            return "Error: Invalid function name."
            
        # Clean up code (remove shebangs, ensure indentation)
        code = code.strip()
        if code.startswith("#!"):
            # Handle potential shebangs
            lines = code.split("\n")
            if lines[0].startswith("#!"):
                code = "\n".join(lines[1:]).strip()
            
        function_def = f"\n\nfunction {name}() {{\n    {code}\n}}"
        
        # --- Transactional Safety Check ---
        # 1. Read existing content
        try:
            with open("skills.sh", "r") as f:
                original_content = f.read()
        except FileNotFoundError:
            original_content = "#!/bin/bash\n"

        # 2. Try writing to a temporary file
        temp_file = "skills.temp.sh"
        with open(temp_file, "w") as f:
            f.write(original_content + function_def)
            
        # 3. Test if the new file is valid bash (try to source it)
        # We use `bash -n` for syntax check, but `source` is better for runtime logic check if needed.
        # However, `source` executes code, which might be risky. `bash -n` is safer for syntax.
        check = subprocess.run(
            ["bash", "-n", temp_file],
            capture_output=True,
            text=True
        )
        
        if check.returncode != 0:
            import os
            os.remove(temp_file)
            return f"Error: The provided code has syntax errors and was NOT added.\nDetails: {check.stderr}"
            
        # 4. If valid, commit to main file
        import os
        os.rename(temp_file, "skills.sh")
        
        return f"Skill '{name}' added successfully and verified."
    except Exception as e:
        return f"Error adding skill: {str(e)}"
