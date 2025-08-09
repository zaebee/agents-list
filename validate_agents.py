#!/usr/bin/env python3
"""
Agent validation and model assignment audit script.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Expected model assignments based on README documentation
EXPECTED_MODEL_ASSIGNMENTS = {
    'haiku': [
        'data-scientist', 'api-documenter', 'reference-builder', 'business-analyst',
        'content-marketer', 'customer-support', 'sales-automator', 'search-specialist',
        'legal-advisor'
    ],
    'sonnet': [
        'python-pro', 'javascript-pro', 'typescript-pro', 'golang-pro', 'rust-pro',
        'c-pro', 'cpp-pro', 'php-pro', 'java-pro', 'elixir-pro', 'csharp-pro',
        'scala-pro', 'unity-developer', 'minecraft-bukkit-pro', 'ios-developer',
        'frontend-developer', 'ui-ux-designer', 'backend-architect', 'mobile-developer',
        'sql-pro', 'graphql-architect', 'devops-troubleshooter', 'deployment-engineer',
        'database-optimizer', 'database-admin', 'terraform-specialist', 'network-engineer',
        'dx-optimizer', 'data-engineer', 'test-automator', 'code-reviewer', 'debugger',
        'error-detective', 'ml-engineer', 'legacy-modernizer', 'payment-integration',
        'mermaid-expert'
    ],
    'opus': [
        'ai-engineer', 'security-auditor', 'performance-engineer', 'incident-responder',
        'mlops-engineer', 'architect-reviewer', 'cloud-architect', 'prompt-engineer',
        'context-manager', 'quant-analyst', 'risk-manager', 'docs-architect',
        'tutorial-engineer'
    ]
}

def parse_agent_file(file_path: Path) -> Dict:
    """Parse agent markdown file and extract metadata."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if not frontmatter_match:
            return {"error": "No frontmatter found"}
        
        frontmatter = frontmatter_match.group(1)
        
        # Parse frontmatter fields
        metadata = {}
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
        
        return metadata
    except Exception as e:
        return {"error": str(e)}

def audit_model_assignments() -> Dict:
    """Audit current model assignments against expected assignments."""
    agents_dir = Path('.')
    agent_files = list(agents_dir.glob('*.md'))
    agent_files = [f for f in agent_files if f.name not in ['README.md']]
    
    current_assignments = {'haiku': [], 'sonnet': [], 'opus': [], 'missing': [], 'errors': []}
    
    for agent_file in agent_files:
        agent_name = agent_file.stem
        metadata = parse_agent_file(agent_file)
        
        if "error" in metadata:
            current_assignments['errors'].append({
                'agent': agent_name,
                'error': metadata['error']
            })
            continue
        
        model = metadata.get('model', 'missing')
        if model == 'missing':
            current_assignments['missing'].append(agent_name)
        elif model in current_assignments:
            current_assignments[model].append(agent_name)
        else:
            current_assignments['errors'].append({
                'agent': agent_name,
                'error': f'Invalid model: {model}'
            })
    
    return current_assignments

def generate_corrections() -> List[Dict]:
    """Generate list of corrections needed for proper model assignment."""
    current = audit_model_assignments()
    corrections = []
    
    # Find agents that need model corrections
    for expected_model, expected_agents in EXPECTED_MODEL_ASSIGNMENTS.items():
        for agent in expected_agents:
            # Find current model for this agent
            current_model = None
            for model, agents in current.items():
                if model in ['haiku', 'sonnet', 'opus'] and agent in agents:
                    current_model = model
                    break
            
            if current_model != expected_model:
                corrections.append({
                    'agent': agent,
                    'current_model': current_model or 'missing',
                    'expected_model': expected_model,
                    'file_path': f'{agent}.md'
                })
    
    return corrections

def get_all_agent_names() -> List[str]:
    """Get all agent names from markdown files."""
    agents_dir = Path('.')
    agent_files = list(agents_dir.glob('*.md'))
    agent_files = [f for f in agent_files if f.name not in ['README.md']]
    
    return [f.stem for f in agent_files]

def main():
    """Main function to run the audit."""
    print("=== Agent Model Assignment Audit ===\n")
    
    # Current state
    current = audit_model_assignments()
    print("Current Model Distribution:")
    for model, agents in current.items():
        if model in ['haiku', 'sonnet', 'opus']:
            print(f"  {model}: {len(agents)} agents")
    print(f"  missing model: {len(current['missing'])} agents")
    print(f"  errors: {len(current['errors'])} agents")
    
    if current['missing']:
        print(f"\nAgents missing model assignment:")
        for agent in current['missing']:
            print(f"  - {agent}")
    
    if current['errors']:
        print(f"\nAgents with errors:")
        for error in current['errors']:
            print(f"  - {error['agent']}: {error['error']}")
    
    # Generate corrections
    corrections = generate_corrections()
    if corrections:
        print(f"\n=== Model Assignment Corrections Needed ===")
        print(f"Total corrections needed: {len(corrections)}")
        
        by_model = {}
        for correction in corrections:
            expected = correction['expected_model']
            if expected not in by_model:
                by_model[expected] = []
            by_model[expected].append(correction)
        
        for model, model_corrections in by_model.items():
            print(f"\nAgents that should use {model} model:")
            for correction in model_corrections:
                current = correction['current_model']
                print(f"  - {correction['agent']} (currently: {current})")
    else:
        print("\n✅ All model assignments are correct!")
    
    # All agents list for CRM integration
    all_agents = get_all_agent_names()
    print(f"\n=== All Available Agents ({len(all_agents)}) ===")
    print("For CRM integration:")
    print(json.dumps(all_agents, indent=2))

if __name__ == "__main__":
    main()