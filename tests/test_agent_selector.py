#!/usr/bin/env python3
"""
Unit tests for the AI agent selector functionality.
"""

import unittest
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "our-crm-ai"))

from agent_selector import suggest_agents, AGENT_KEYWORDS, EnhancedAgentSelector


class TestAgentSelector(unittest.TestCase):
    """Test cases for AI agent selector functionality."""

    def test_python_task_suggestion(self):
        """Test that Python-related tasks suggest python-pro agent."""
        task = "optimize python database queries using pandas"
        suggestions = suggest_agents(task, max_suggestions=5)

        self.assertGreater(len(suggestions), 0, "Should return at least one suggestion")

        # Check that python-pro is in top suggestions
        agent_names = [s["agent"] for s in suggestions]
        self.assertIn(
            "python-pro", agent_names, "python-pro should be suggested for Python tasks"
        )

        # Check confidence scores are reasonable
        for suggestion in suggestions:
            self.assertGreater(
                suggestion["confidence"], 0, "Confidence should be positive"
            )
            self.assertLessEqual(
                suggestion["confidence"], 100, "Confidence should not exceed 100%"
            )

    def test_database_task_suggestion(self):
        """Test that database tasks suggest appropriate agents."""
        task = "slow query optimization and index design"
        suggestions = suggest_agents(task, max_suggestions=3)

        agent_names = [s["agent"] for s in suggestions]

        # Should suggest database-related agents
        database_agents = ["database-optimizer", "sql-pro", "performance-engineer"]
        found_database_agent = any(agent in agent_names for agent in database_agents)
        self.assertTrue(
            found_database_agent, "Should suggest at least one database-related agent"
        )

    def test_security_task_suggestion(self):
        """Test that security tasks suggest security-auditor."""
        task = "review authentication vulnerabilities and implement JWT security"
        suggestions = suggest_agents(task, max_suggestions=3)

        agent_names = [s["agent"] for s in suggestions]
        self.assertIn(
            "security-auditor",
            agent_names,
            "security-auditor should be suggested for security tasks",
        )

    

    def test_empty_task_handling(self):
        """Test handling of empty or invalid task descriptions."""
        suggestions = suggest_agents("", max_suggestions=3)
        self.assertEqual(len(suggestions), 0, "Empty task should return no suggestions")

        suggestions = suggest_agents("   ", max_suggestions=3)  # Whitespace only
        self.assertEqual(
            len(suggestions), 0, "Whitespace-only task should return no suggestions"
        )

    def test_keyword_matching(self):
        """Test that keyword matching works correctly."""
        # Test specific keyword combinations
        test_cases = [
            ("react native mobile app", ["mobile-developer", "frontend-developer"]),
            (
                "terraform infrastructure deployment",
                ["terraform-specialist", "deployment-engineer"],
            ),
            ("unity game development", ["unity-developer"]),
            ("machine learning model training", ["ml-engineer", "ai-engineer"]),
        ]

        for task, expected_agents in test_cases:
            suggestions = suggest_agents(task, max_suggestions=5)
            agent_names = [s["agent"] for s in suggestions]

            # Check that at least one expected agent is suggested
            found_expected = any(agent in agent_names for agent in expected_agents)
            self.assertTrue(
                found_expected,
                f"Task '{task}' should suggest at least one of {expected_agents}, got {agent_names}",
            )

    def test_agent_keywords_coverage(self):
        """Test that all agents have defined keywords."""
        # Check that we have keywords for major agent categories
        required_agents = [
            "python-pro",
            "javascript-pro",
            "security-auditor",
            "database-optimizer",
            "frontend-developer",
        ]

        for agent in required_agents:
            self.assertIn(
                agent, AGENT_KEYWORDS, f"Agent {agent} should have defined keywords"
            )
            self.assertGreater(
                len(AGENT_KEYWORDS[agent]),
                0,
                f"Agent {agent} should have non-empty keywords",
            )

    def test_enhanced_agent_selector(self):
        """Test the EnhancedAgentSelector class."""
        import asyncio
        selector = EnhancedAgentSelector(enable_semantic=False)
        asyncio.run(selector.initialize())
        task = "python web development"
        suggestions = asyncio.run(selector.suggest_agents(task))
        self.assertIsInstance(suggestions, list)
        if suggestions:
            suggestion = suggestions[0]
            self.assertTrue(hasattr(suggestion, "agent_name"))
            self.assertTrue(hasattr(suggestion, "confidence"))
            self.assertTrue(hasattr(suggestion, "reasoning"))
            self.assertTrue(hasattr(suggestion, "matched_keywords"))
            self.assertGreater(suggestion.confidence, 0)


class TestAgentSelectorIntegration(unittest.TestCase):
    """Integration tests for agent selector."""

    def test_real_world_scenarios(self):
        """Test with realistic task descriptions."""
        scenarios = [
            {
                "task": "implement user authentication with OAuth2 and JWT tokens",
                "expected_categories": ["security", "backend", "api"],
            },
            {
                "task": "optimize slow PostgreSQL queries and add proper indexing",
                "expected_categories": ["database", "performance"],
            },
            {
                "task": "build responsive React dashboard with real-time updates",
                "expected_categories": ["frontend", "javascript"],
            },
            {
                "task": "deploy microservices to Kubernetes with Terraform",
                "expected_categories": ["infrastructure", "deployment"],
            },
        ]

        for scenario in scenarios:
            suggestions = suggest_agents(scenario["task"], max_suggestions=3)
            self.assertGreater(
                len(suggestions), 0, f"Should suggest agents for: {scenario['task']}"
            )

            # Check that suggestions make sense (this is more of a sanity check)
            for suggestion in suggestions:
                self.assertIn("agent", suggestion)
                self.assertIn("confidence", suggestion)
                self.assertIn("matched_keywords", suggestion)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
