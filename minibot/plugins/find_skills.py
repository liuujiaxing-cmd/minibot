from ..tools import tool
import requests
import os

# --- SKILL METADATA ---
# Description: Find available skills (local and remote).
# Input: query (string)
# Output: List of matching skills.

MOCK_VERCEL_SKILLS = {
    "vercel-labs/agent-skills": [
        "react-best-practices",
        "web-design-guidelines",
        "react-native-guidelines",
        "composition-patterns",
        "vercel-deploy-claimable"
    ],
    "composio/awesome-claude-skills": [
        "linear-integration",
        "notion-integration"
    ]
}

@tool(name="find_skills", description="Find skills to install or use. Search for capabilities like 'react', 'deploy', 'testing'. Usage: find_skills(query='react')")
def find_skills(query: str):
    """
    Search for skills in the Vercel ecosystem and local registry.
    This simulates `npx skills find <query>`.
    """
    query = query.lower()
    results = []
    
    # 1. Search Local Installed Skills
    # (Assuming we store them in minibot/plugins/)
    local_plugins = []
    plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
    if os.path.exists(plugins_dir):
        for f in os.listdir(plugins_dir):
            if f.endswith(".py") and f != "__init__.py":
                local_plugins.append(f.replace(".py", ""))
    
    for skill in local_plugins:
        if query in skill:
            results.append(f"📦 [Local] {skill} (Already installed)")

    # 2. Search Remote Vercel Skills (Mocked for now, in real life we'd query an API or GitHub)
    for repo, skills in MOCK_VERCEL_SKILLS.items():
        for skill in skills:
            if query in skill or query in repo:
                results.append(f"☁️ [Remote] {repo}@{skill}")
                
    if not results:
        return f"No skills found for '{query}'. Try broader terms like 'react', 'deploy', 'web'."
        
    return "Found skills:\n" + "\n".join(results) + "\n\nTo install a remote skill, use `add_skill_from_git` (supports documentation-only SKILL.md and executable skill packs via skillpack.json)."
