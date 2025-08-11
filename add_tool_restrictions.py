#!/usr/bin/env python3
"""
Add appropriate tool restrictions to agent files based on their roles.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set

# Tool categories and their appropriate usage contexts
TOOL_SETS = {
    # Core development tools - most agents need these
    "core": ["Read", "Edit", "MultiEdit", "Grep", "Glob", "LS"],
    # Code execution and system operations
    "execution": ["Bash", "Write"],
    # Web and research
    "web": ["WebFetch", "WebSearch"],
    # Task coordination
    "task": ["Task", "TodoWrite"],
    # Specialized
    "notebook": ["NotebookEdit"],
    "process": ["BashOutput", "KillBash"],
    "plan": ["ExitPlanMode"],
}

# Agent categories and their appropriate tool sets
AGENT_TOOL_RESTRICTIONS = {
    # Language specialists - need full development tools
    "language_specialists": {
        "agents": [
            "python-pro",
            "javascript-pro",
            "typescript-pro",
            "golang-pro",
            "rust-pro",
            "java-pro",
            "csharp-pro",
            "cpp-pro",
            "c-pro",
            "php-pro",
            "scala-pro",
            "elixir-pro",
            "sql-pro",
        ],
        "tools": ["core", "execution", "task", "notebook"],
    },
    # Architecture and design - need analysis and web research
    "architects": {
        "agents": [
            "backend-architect",
            "architect-reviewer",
            "cloud-architect",
            "graphql-architect",
        ],
        "tools": ["core", "execution", "web", "task", "plan"],
    },
    # Frontend and UI - need core tools plus execution
    "frontend": {
        "agents": [
            "frontend-developer",
            "ui-ux-designer",
            "mobile-developer",
            "ios-developer",
            "unity-developer",
        ],
        "tools": ["core", "execution", "web", "task"],
    },
    # Infrastructure and operations - need full system access
    "infrastructure": {
        "agents": [
            "devops-troubleshooter",
            "deployment-engineer",
            "terraform-specialist",
            "network-engineer",
            "incident-responder",
            "database-admin",
            "database-optimizer",
        ],
        "tools": ["core", "execution", "web", "task", "process"],
    },
    # Security and auditing - restricted execution, enhanced analysis
    "security": {
        "agents": ["security-auditor", "code-reviewer"],
        "tools": ["core", "web", "task"],  # No direct execution for security
    },
    # Data and AI - need research and execution
    "data_ai": {
        "agents": [
            "ai-engineer",
            "ml-engineer",
            "mlops-engineer",
            "data-engineer",
            "data-scientist",
            "prompt-engineer",
        ],
        "tools": ["core", "execution", "web", "task", "notebook"],
    },
    # Documentation and content - primarily analysis and web research
    "documentation": {
        "agents": [
            "docs-architect",
            "api-documenter",
            "reference-builder",
            "tutorial-engineer",
            "content-marketer",
            "mermaid-expert",
        ],
        "tools": ["core", "web", "task"],
    },
    # Business and support - mainly web research and analysis
    "business": {
        "agents": [
            "business-analyst",
            "sales-automator",
            "customer-support",
            "legal-advisor",
            "risk-manager",
            "quant-analyst",
        ],
        "tools": ["core", "web", "task"],
    },
    # Quality and testing - need execution for testing
    "quality": {
        "agents": [
            "test-automator",
            "debugger",
            "error-detective",
            "performance-engineer",
        ],
        "tools": ["core", "execution", "web", "task", "process"],
    },
    # Search and research specialists - enhanced web capabilities
    "research": {"agents": ["search-specialist"], "tools": ["core", "web", "task"]},
    # Specialized tools
    "specialized": {
        "agents": [
            "payment-integration",
            "legacy-modernizer",
            "minecraft-bukkit-pro",
            "dx-optimizer",
            "context-manager",
        ],
        "tools": ["core", "execution", "web", "task"],
    },
}


def expand_tool_categories(tool_categories: List[str]) -> List[str]:
    """Expand tool category names to actual tool names."""
    tools = set()
    for category in tool_categories:
        if category in TOOL_SETS:
            tools.update(TOOL_SETS[category])
    return sorted(list(tools))


def get_agent_category(agent_name: str) -> str:
    """Find which category an agent belongs to."""
    for category, config in AGENT_TOOL_RESTRICTIONS.items():
        if agent_name in config["agents"]:
            return category
    return "specialized"  # default category


def update_agent_tools(agent_file: Path) -> bool:
    """Update an agent file with appropriate tool restrictions."""
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

        # Determine appropriate tools for this agent
        agent_name = agent_file.stem
        category = get_agent_category(agent_name)

        if category not in AGENT_TOOL_RESTRICTIONS:
            print(f"❌ No tool restrictions defined for category: {category}")
            return False

        tool_categories = AGENT_TOOL_RESTRICTIONS[category]["tools"]
        tools = expand_tool_categories(tool_categories)
        tools_line = f"tools: {', '.join(tools)}"

        # Insert tools line before closing ---
        updated_frontmatter = frontmatter.rstrip("---\n") + f"{tools_line}\n---\n"
        updated_content = updated_frontmatter + rest_of_file

        # Write back
        with open(agent_file, "w", encoding="utf-8") as f:
            f.write(updated_content)

        print(
            f"✅ Updated {agent_file.stem} ({category}) with tools: {', '.join(tools)}"
        )
        return True

    except Exception as e:
        print(f"❌ Error updating {agent_file.name}: {e}")
        return False


def main():
    """Add tool restrictions to all agent files."""
    print("🔧 Adding Tool Restrictions to Agent Files")
    print("=" * 50)

    # Find all agent files
    agents_dir = Path(".")
    agent_files = list(agents_dir.glob("*.md"))
    agent_files = [f for f in agent_files if f.name not in ["README.md"]]

    print(f"Found {len(agent_files)} agent files")

    # Show tool restriction plan
    print(f"\n📋 Tool Restriction Plan:")
    for category, config in AGENT_TOOL_RESTRICTIONS.items():
        tools = expand_tool_categories(config["tools"])
        print(f"\n📁 {category} ({len(config['agents'])} agents):")
        print(f"   Tools: {', '.join(tools)}")
        print(
            f"   Agents: {', '.join(config['agents'][:3])}{'...' if len(config['agents']) > 3 else ''}"
        )

    proceed = (
        input(f"\nProceed with updating {len(agent_files)} agent files? (y/N): ")
        .strip()
        .lower()
    )
    if proceed != "y":
        print("Operation cancelled.")
        return

    # Update files
    updated_count = 0
    skipped_count = 0
    error_count = 0

    print(f"\n🚀 Processing files...")
    for agent_file in sorted(agent_files):
        result = update_agent_tools(agent_file)
        if result:
            updated_count += 1
        elif "already has tools" in str(result):
            skipped_count += 1
        else:
            error_count += 1

    print(f"\n📊 Summary:")
    print(f"   ✅ Updated: {updated_count}")
    print(f"   ⚠️  Skipped: {skipped_count}")
    print(f"   ❌ Errors: {error_count}")

    if updated_count > 0:
        print(f"\n🎉 Successfully added tool restrictions to {updated_count} agents!")


if __name__ == "__main__":
    main()
