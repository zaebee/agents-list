#!/usr/bin/env python3
"""
Apply tool restrictions to a sample of agent files as demonstration.
"""

import os
import re
from pathlib import Path
from typing import Dict, List

# Tool categories and their appropriate usage contexts
TOOL_SETS = {
    "core": ["Read", "Edit", "MultiEdit", "Grep", "Glob", "LS"],
    "execution": ["Bash", "Write"],
    "web": ["WebFetch", "WebSearch"],
    "task": ["Task", "TodoWrite"],
    "notebook": ["NotebookEdit"],
    "process": ["BashOutput", "KillBash"],
    "plan": ["ExitPlanMode"],
}

# Sample agents to update as demonstration
SAMPLE_UPDATES = {
    "python-pro": ["core", "execution", "task", "notebook"],
    "frontend-developer": ["core", "execution", "web", "task"],
    "devops-troubleshooter": ["core", "execution", "web", "task", "process"],
    "api-documenter": ["core", "web", "task"],
    "business-analyst": ["core", "web", "task"],
}


def expand_tool_categories(tool_categories: List[str]) -> List[str]:
    """Expand tool category names to actual tool names."""
    tools = set()
    for category in tool_categories:
        if category in TOOL_SETS:
            tools.update(TOOL_SETS[category])
    return sorted(list(tools))


def update_agent_tools(agent_file: Path, tool_categories: List[str]) -> bool:
    """Update an agent file with specific tool restrictions."""
    try:
        with open(agent_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract frontmatter
        frontmatter_match = re.match(r"^(---\n.*?\n---\n)", content, re.DOTALL)
        if not frontmatter_match:
            print(f"❌ No frontmatter found in {agent_file.name}")
            return False

        frontmatter = frontmatter_match.group(1)
        rest_of_file = content[len(frontmatter) :]

        # Check if tools already exists
        if "tools:" in frontmatter:
            print(f"⚠️  {agent_file.stem} already has tools defined")
            return False

        # Determine appropriate tools
        tools = expand_tool_categories(tool_categories)
        tools_line = f"tools: {', '.join(tools)}"

        # Insert tools line before closing ---
        updated_frontmatter = frontmatter.rstrip("---\n") + f"{tools_line}\n---\n"
        updated_content = updated_frontmatter + rest_of_file

        # Write back
        with open(agent_file, "w", encoding="utf-8") as f:
            f.write(updated_content)

        print(f"✅ Updated {agent_file.stem} with tools: {', '.join(tools)}")
        return True

    except Exception as e:
        print(f"❌ Error updating {agent_file.name}: {e}")
        return False


def main():
    """Apply tool restrictions to sample agent files."""
    print("🔧 Applying Tool Restrictions to Sample Agents")
    print("=" * 50)

    updated_count = 0

    for agent_name, tool_categories in SAMPLE_UPDATES.items():
        agent_file = Path(f"{agent_name}.md")

        if not agent_file.exists():
            print(f"❌ File not found: {agent_file}")
            continue

        tools = expand_tool_categories(tool_categories)
        print(f"\n📝 {agent_name}:")
        print(f"   Categories: {', '.join(tool_categories)}")
        print(f"   Tools: {', '.join(tools)}")

        if update_agent_tools(agent_file, tool_categories):
            updated_count += 1

    print(
        f"\n📊 Summary: Updated {updated_count}/{len(SAMPLE_UPDATES)} sample agents with tool restrictions"
    )


if __name__ == "__main__":
    main()
