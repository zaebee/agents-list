#!/usr/bin/env python3
"""
AI Agent Selector - Automatically suggests appropriate agents for tasks.
"""

import re
import difflib
from typing import List, Tuple, Dict
from pathlib import Path

# Agent categories and keywords for intelligent task routing
AGENT_KEYWORDS = {
    # Programming Languages
    'python-pro': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'py', 'pip', 'pytest'],
    'javascript-pro': ['javascript', 'js', 'node', 'npm', 'react', 'vue', 'angular', 'express'],
    'typescript-pro': ['typescript', 'ts', 'type', 'interface', 'generic', 'tsc'],
    'golang-pro': ['go', 'golang', 'goroutine', 'channel', 'gin', 'echo', 'mod'],
    'rust-pro': ['rust', 'cargo', 'ownership', 'lifetime', 'borrow', 'tokio', 'serde'],
    'java-pro': ['java', 'spring', 'maven', 'gradle', 'jvm', 'kotlin', 'hibernate'],
    'csharp-pro': ['c#', 'csharp', 'dotnet', '.net', 'asp.net', 'entity framework', 'nuget'],
    'cpp-pro': ['c++', 'cpp', 'stl', 'boost', 'cmake', 'template', 'raii'],
    'c-pro': ['c language', 'embedded', 'system call', 'memory', 'pointer', 'malloc'],
    'php-pro': ['php', 'laravel', 'symfony', 'composer', 'wordpress'],
    'scala-pro': ['scala', 'akka', 'spark', 'sbt', 'functional programming', 'cats', 'zio'],
    'elixir-pro': ['elixir', 'phoenix', 'otp', 'erlang', 'genserver', 'supervisor'],
    'sql-pro': ['sql', 'database', 'query', 'mysql', 'postgresql', 'sqlite', 'index'],
    
    # Frontend & Mobile
    'frontend-developer': ['frontend', 'ui', 'component', 'css', 'html', 'responsive', 'browser'],
    'ui-ux-designer': ['design', 'wireframe', 'prototype', 'user experience', 'accessibility', 'figma'],
    'mobile-developer': ['mobile', 'react native', 'flutter', 'ios', 'android', 'app store'],
    'ios-developer': ['ios', 'swift', 'swiftui', 'xcode', 'app store', 'iphone', 'ipad'],
    'unity-developer': ['unity', 'game', 'c# script', 'gameobject', '3d', '2d', 'animation'],
    
    # Architecture & Backend
    'backend-architect': ['api', 'microservice', 'architecture', 'service', 'endpoint', 'restful'],
    'architect-reviewer': ['architecture', 'design pattern', 'solid', 'review', 'structure'],
    'graphql-architect': ['graphql', 'schema', 'resolver', 'federation', 'apollo'],
    
    # Infrastructure & DevOps
    'cloud-architect': ['aws', 'azure', 'gcp', 'cloud', 'serverless', 'lambda', 'infrastructure'],
    'devops-troubleshooter': ['deployment', 'pipeline', 'build', 'ci/cd', 'docker', 'logs'],
    'deployment-engineer': ['deploy', 'ci/cd', 'pipeline', 'docker', 'kubernetes', 'github actions'],
    'terraform-specialist': ['terraform', 'infrastructure', 'iac', 'hcl', 'tfstate'],
    'network-engineer': ['network', 'dns', 'ssl', 'tls', 'load balancer', 'proxy', 'firewall'],
    'incident-responder': ['outage', 'down', 'incident', 'emergency', 'urgent', 'critical'],
    
    # Database & Data
    'database-optimizer': ['slow query', 'performance', 'index', 'optimization', 'explain'],
    'database-admin': ['backup', 'replication', 'migration', 'database admin', 'user', 'permission'],
    'data-scientist': ['analysis', 'sql', 'bigquery', 'data', 'insight', 'report', 'metrics'],
    'data-engineer': ['etl', 'pipeline', 'airflow', 'kafka', 'stream', 'warehouse'],
    
    # AI & ML
    'ai-engineer': ['llm', 'openai', 'anthropic', 'rag', 'vector', 'embedding', 'chatbot'],
    'ml-engineer': ['machine learning', 'tensorflow', 'pytorch', 'model', 'training'],
    'mlops-engineer': ['mlflow', 'kubeflow', 'experiment', 'model registry', 'ml pipeline'],
    'prompt-engineer': ['prompt', 'llm optimization', 'ai prompt', 'language model'],
    
    # Security & Quality
    'security-auditor': ['security', 'vulnerability', 'owasp', 'auth', 'encryption', 'jwt'],
    'code-reviewer': ['code review', 'quality', 'best practice', 'refactor'],
    'test-automator': ['test', 'testing', 'unit test', 'integration', 'e2e', 'mock'],
    'debugger': ['debug', 'error', 'bug', 'issue', 'troubleshoot', 'fix'],
    'error-detective': ['log', 'trace', 'exception', 'error analysis', 'investigation'],
    
    # Performance & Monitoring
    'performance-engineer': ['performance', 'optimization', 'bottleneck', 'slow', 'cache'],
    'search-specialist': ['search', 'research', 'investigation', 'analysis', 'competitive'],
    
    # Documentation & Content
    'docs-architect': ['documentation', 'technical writing', 'manual', 'guide'],
    'api-documenter': ['api doc', 'openapi', 'swagger', 'endpoint documentation'],
    'reference-builder': ['reference', 'api reference', 'parameter', 'configuration'],
    'tutorial-engineer': ['tutorial', 'guide', 'learning', 'educational', 'walkthrough'],
    'mermaid-expert': ['diagram', 'flowchart', 'sequence', 'architecture diagram'],
    'content-marketer': ['blog', 'content', 'marketing', 'seo', 'social media'],
    
    # Business & Support
    'business-analyst': ['metrics', 'kpi', 'analytics', 'business', 'revenue', 'growth'],
    'sales-automator': ['sales', 'email', 'lead', 'proposal', 'cold outreach'],
    'customer-support': ['support', 'help', 'faq', 'customer', 'ticket'],
    'legal-advisor': ['privacy', 'terms', 'legal', 'gdpr', 'compliance', 'policy'],
    'risk-manager': ['risk', 'portfolio', 'trading', 'position', 'hedge'],
    'quant-analyst': ['financial', 'trading', 'backtest', 'strategy', 'market data'],
    
    # Specialized
    'payment-integration': ['payment', 'stripe', 'paypal', 'checkout', 'billing'],
    'legacy-modernizer': ['legacy', 'migration', 'modernize', 'refactor', 'upgrade'],
    'minecraft-bukkit-pro': ['minecraft', 'bukkit', 'spigot', 'plugin', 'server'],
    'dx-optimizer': ['developer experience', 'tooling', 'workflow', 'setup'],
    'context-manager': ['multi-agent', 'coordination', 'context', 'workflow']
}

def fuzzy_keyword_match(text: str, keyword: str, threshold: float = 0.8) -> bool:
    """Use fuzzy matching for more flexible keyword detection."""
    words = text.lower().split()
    keyword_lower = keyword.lower()
    
    # Direct substring match (fastest)
    if keyword_lower in text.lower():
        return True
    
    # Fuzzy match against individual words
    for word in words:
        if difflib.SequenceMatcher(None, word, keyword_lower).ratio() >= threshold:
            return True
    
    # Fuzzy match against word combinations for multi-word keywords
    if ' ' in keyword_lower:
        keyword_words = keyword_lower.split()
        text_words = words
        
        for i in range(len(text_words) - len(keyword_words) + 1):
            text_phrase = ' '.join(text_words[i:i + len(keyword_words)])
            if difflib.SequenceMatcher(None, text_phrase, keyword_lower).ratio() >= threshold:
                return True
    
    return False

def calculate_agent_scores(task_description: str) -> List[Tuple[str, float, List[str]]]:
    """Calculate relevance scores for each agent based on task description with fuzzy matching."""
    task_lower = task_description.lower()
    scores = []
    
    for agent, keywords in AGENT_KEYWORDS.items():
        matched_keywords = []
        score = 0.0
        
        for keyword in keywords:
            match_type = None
            
            # Exact match (highest weight)
            if keyword.lower() in task_lower:
                match_type = "exact"
                matched_keywords.append(keyword)
                keyword_weight = len(keyword.split()) * 1.0
                score += keyword_weight
            
            # Fuzzy match (lower weight)
            elif fuzzy_keyword_match(task_lower, keyword, threshold=0.75):
                match_type = "fuzzy"
                matched_keywords.append(f"~{keyword}")  # Mark as fuzzy match
                keyword_weight = len(keyword.split()) * 0.7  # Reduced weight for fuzzy matches
                score += keyword_weight
        
        if matched_keywords:
            scores.append((agent, score, matched_keywords))
    
    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores

def suggest_agents(task_description: str, max_suggestions: int = 5) -> List[Dict]:
    """Suggest the most appropriate agents for a given task."""
    scores = calculate_agent_scores(task_description)
    
    suggestions = []
    for agent, score, keywords in scores[:max_suggestions]:
        if score > 0:  # Only include agents with positive scores
            suggestions.append({
                'agent': agent,
                'confidence': min(score * 10, 100),  # Convert to percentage, cap at 100%
                'matched_keywords': keywords,
                'reasoning': f"Matched keywords: {', '.join(keywords)}"
            })
    
    return suggestions

def main():
    """Interactive agent suggestion tool."""
    print("🤖 AI Agent Selector")
    print("=" * 50)
    print("Enter task descriptions to get agent suggestions.")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            task = input("Task description: ").strip()
            if task.lower() in ['quit', 'exit', 'q']:
                break
            
            if not task:
                continue
            
            suggestions = suggest_agents(task)
            
            if suggestions:
                print(f"\n📋 Suggested agents for: '{task}'")
                print("-" * 50)
                
                for i, suggestion in enumerate(suggestions, 1):
                    confidence = suggestion['confidence']
                    agent = suggestion['agent']
                    keywords = ', '.join(suggestion['matched_keywords'])
                    
                    print(f"{i}. {agent} ({confidence:.1f}% confidence)")
                    print(f"   Matched: {keywords}")
                
                # Show top recommendation
                top_agent = suggestions[0]['agent']
                print(f"\n💡 Recommended: {top_agent}")
            else:
                print("❌ No specific agent suggestions found.")
                print("💡 Consider using 'search-specialist' for general research tasks.")
            
            print()
        
        except KeyboardInterrupt:
            break
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()